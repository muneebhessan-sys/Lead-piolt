import base64, hashlib, hmac, json, logging, re, secrets, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, get_db
from app.models import (
    Account, AdminSetting, AuditLog, Business, BusinessSocialProfile, Call, Campaign, CampaignItem,
    CallStatus, Customer, InstructionProfile, InstructionVersion, Integration, Job, Lead, Message, MessageTemplate,
    Note, OAuthState, OutboundMessage, OutboundMessageStatus, Payment, Project, ServiceProfile,
    SystemSetting, TimelineEvent, VoiceAgentConfig, VoiceAgent, WebsiteAudit
)
from app.services.audit import audit_website
from app.services.intelligence import IntelligenceEngine
from app.services.jobs import LocalJobEngine
from app.services.google_places import GooglePlacesError, GooglePlacesProvider, normalize_place
from app.services.message_composer import MessageComposerEngine
from app.services.message_engine.factory import MessageEngineFactory
from app.services.messaging import MessageProviderFactory, OutboundMessageService
from app.services.oauth import OAuthService, StateManager, ProviderRegistry, SafeProfileFetcher
from app.services.security import secret_store
from app.services.voice import LocalVoiceAgentProvider
from app.services.voice.brain.rule_brain import RuleBrain
from app.api.v1.webhooks import router as webhook_router
from workers.dispatcher import CampaignDispatcher

app = FastAPI(title="LeadPilot API", version="0.2.0")
logger = logging.getLogger("leadpilot.oauth")
app.include_router(webhook_router)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "path": request.url.path, "status_code": exc.status_code})


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail, "path": request.url.path, "status_code": exc.status_code})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "VALIDATION_ERROR", "path": request.url.path, "status_code": 422, "details": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "INTERNAL_SERVER_ERROR", "path": request.url.path, "status_code": 500})


jobs = LocalJobEngine()
oauth_service = OAuthService()
profile_fetcher = SafeProfileFetcher()
campaign_dispatcher = CampaignDispatcher()
message_engine_factory = MessageEngineFactory()
voice_brains: dict[str, RuleBrain] = {}


def create_admin_token(username: str, role: str = "admin") -> str:
    payload = {"sub": username, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not settings.admin_auth_enabled:
        return {"username": settings.admin_username, "role": "admin"}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN") from exc
    return {"username": payload.get("sub", settings.admin_username), "role": payload.get("role", "admin")}


class InstructionIn(BaseModel):
    name: str = Field(min_length=1, max_length=160); niche: str=""; language: str="English"; tone: str="Professional"; offer: str=""; services: str=""; cta: str=""; rules: str=""; do_not_say: str=""; personalization_rules: str=""; additional_instructions: str=""; active: bool=True
class JobIn(BaseModel):
    job_type: str = Field(min_length=1, max_length=80); payload: dict={}; total: int=Field(default=0, ge=0, le=500)
class VoiceIn(BaseModel):
    name:str="Local voice agent"; base_url:str=""; health_path:str="/health"; call_path:str="/calls"; enabled:bool=False
class DiscoveryIn(BaseModel):
    niche:str=Field(min_length=1,max_length=160); location:str=Field(min_length=1,max_length=200); keywords:str=""; limit:int=Field(default=20,ge=1,le=60)
class ServiceIn(BaseModel):
    company_name:str=""; description:str=""; services:str=""; target_niches:str=""; target_locations:str=""; offer:str=""; portfolio_url:str=""; contact_information:str=""; cta:str=""; preferred_tone:str="Professional"; additional_instructions:str=""
class DraftIn(BaseModel): instruction_profile_id:int|None=None; recipient:str=""; channel:str="EMAIL"
class AIPreviewIn(BaseModel):
    business_name: str = "Unknown business"
    website: str = ""
    website_status: str = "unknown"
    previous_conversation: str = ""
    custom_instruction: str = ""
    instruction_profile_id: int | None = None
    channel: str = "EMAIL"
class MessageSendIn(BaseModel):
    recipient: str = Field(min_length=1, max_length=320)
    channel: str = Field(default="EMAIL", min_length=2, max_length=30)
    subject: str = ""
    body: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=255)
    lead_id: int | None = None
    campaign_id: int | None = None
    account_id: int | None = None
class StatusIn(BaseModel): status: str = Field(min_length=1, max_length=30)
class CustomerIn(BaseModel): notes: str = ""
class ProjectIn(BaseModel): name:str=Field(min_length=1,max_length=200); description:str=""; status:str="PLANNED"; start_date:str|None=None; due_date:str|None=None; amount:int=Field(default=0,ge=0); notes:str=""
class NoteIn(BaseModel): content:str=Field(min_length=1)
class PaymentIn(BaseModel): amount:int=Field(ge=0); currency:str="USD"; provider:str=""; status:str="PENDING"; reference:str=""
class CampaignIn(BaseModel): name:str=Field(min_length=1,max_length=200); channel:str="EMAIL"; sender_account:str=Field(default="",max_length=320); sender_account_id:int|None=None; instruction_profile_id:int|None=None; lead_ids:list[int]=[]
class OutreachProfileIn(BaseModel):
    portfolio_urls: list[str] = []
    reference_websites: list[str] = []
    sender_name: str = ""
    default_cta: str = "Would you like a quick, no-pressure review?"
class CampaignPrepareIn(BaseModel): lead_ids: list[int] = []
class CampaignSendIn(BaseModel): lead_ids: list[int] = Field(min_length=1); channel: str | None = None; account_id: int | None = None
class IntegrationConfigIn(BaseModel): account_name:str=""; secret_value:str=""; enabled:bool=True
class AdminSettingIn(BaseModel): key: str = Field(min_length=1, max_length=120); value: str = ""; protected: bool = False
class ThemeIn(BaseModel): theme: str = "OBSIDIAN"; reduced_motion: bool = False
class CallStartIn(BaseModel):
    caller_id: str = ""
    to_number: str = ""
    agent_name: str | None = None
class EmailSendIn(BaseModel): recipient:str=Field(min_length=3,max_length=320); subject:str=Field(min_length=1,max_length=300); content:str=Field(min_length=1)
class SocialProfileIn(BaseModel): platform:str=Field(min_length=2,max_length=30); profile_url:str=Field(min_length=8,max_length=2000); username:str|None=None; source:str="USER_STORED"

# OAuth models
class OAuthBeginIn(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    redirect_uri: str = Field(min_length=1, max_length=500)
    extra_scopes: list[str] | None = None
    extra_params: dict[str, str] | None = None
    target_provider: str | None = None

class OAuthCallbackIn(BaseModel):
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)

class AccountConfigureIn(BaseModel):
    account_name: str = ""
    access_token: str = ""
    refresh_token: str = ""
    provider_user_id: str = ""
    token_expires_in: int | None = None
    settings: dict[str, Any] | None = None

class AccountTestIn(BaseModel):
    provider: str = Field(min_length=1, max_length=50)

# Voice models
class VoiceAgentIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    provider: str = "local"
    base_url: str = ""
    api_key: str = ""
    config: dict[str, Any] = {}
    enabled: bool = False

class VoiceCallIn(BaseModel):
    lead_id: int | None = None
    customer_id: int | None = None
    from_number: str = ""
    to_number: str = ""

class VoiceAgentTurnIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    conversation_id: str = "default"

class PhoneVerificationIn(BaseModel):
    code: str = Field(min_length=4, max_length=8)

# Message Template models
class MessageTemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    template_type: str = Field(pattern="^(EMAIL|SMS|VOICE|WHATSAPP)$")
    subject: str = ""
    content: str = Field(min_length=1)
    variables: list[str] = []
    description: str = ""
    is_system: bool = False

class MessageTemplateTestIn(BaseModel):
    template_id: int
    variables: dict[str, str] = {}

# Instruction Version models
class InstructionVersionCaptureIn(BaseModel):
    instruction_profile_id: int
    name: str = Field(min_length=1, max_length=160)
    niche: str = ""
    language: str = "English"
    tone: str = "Professional"
    offer: str = ""
    services: str = ""
    cta: str = ""
    rules: str = ""
    do_not_say: str = ""
    personalization_rules: str = ""
    additional_instructions: str = ""

# Campaign models
class CampaignLaunchIn(BaseModel):
    lead_ids: list[int] = []
    message_template_id: int | None = None
    instruction_version_id: int | None = None

class CampaignControlIn(BaseModel):
    action: str = Field(pattern="^(pause|resume|stop)$")


# System Setting models
class SystemSettingIn(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: str = ""
    value_type: str = Field(default="string", pattern="^(string|int|bool|json)$")
    description: str = ""
    is_secret: bool = False
    category: str = "general"

@app.middleware("http")
async def request_id(request:Request, call_next):
    request_id=str(uuid.uuid4())
    try:
        response=await call_next(request); result="SUCCESS" if response.status_code<400 else "ERROR"; safe_error=""
    except Exception:
        result="ERROR";safe_error="Unhandled request error";raise
    finally:
        db = None
        try:
            db=SessionLocal()
            db.add(AuditLog(
                action=f"{request.method} {request.url.path}",
                subsystem="API",
                result=locals().get("result","ERROR"),
                request_id=request_id,
                safe_error=locals().get("safe_error",""),
            ))
            db.commit()
        except Exception:
            if db is not None:
                try:
                    db.rollback()
                except Exception:
                    pass
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
    response.headers["X-Request-ID"]=request_id; return response
@app.get("/healthz")
def healthz(): return {"status":"OK","service":"leadpilot","database":"SQLITE"}

@app.get("/api/v1/health")
def health(): return {"status":"WORKING","database":"SQLITE","jobs":"LOCAL_PERSISTENT","dry_run":settings.dry_run,"ai":"DETERMINISTIC_LOCAL"}

@app.get("/api/v1/healthz")
def healthz_api(): return {"status":"OK","service":"leadpilot","database":"SQLITE"}

@app.post("/api/v1/audits")
async def audit(payload:dict):
    if not isinstance(payload.get("url"),str): raise HTTPException(422,detail="url is required")
    try:return await audit_website(payload["url"])
    except ValueError as exc:raise HTTPException(422,detail=str(exc)) from exc
    except Exception as exc:raise HTTPException(502,detail="WEBSITE_UNREACHABLE") from exc
@app.get("/api/v1/admin/instructions")
def list_instructions(db:Session=Depends(get_db), admin: dict = Depends(require_admin)): return db.query(InstructionProfile).order_by(InstructionProfile.id.desc()).all()
@app.post("/api/v1/admin/instructions",status_code=201)
def create_instruction(data:InstructionIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    if db.query(InstructionProfile).filter_by(name=data.name).first():raise HTTPException(409,detail="Profile name already exists")
    item=InstructionProfile(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item
@app.put("/api/v1/admin/instructions/{profile_id}")
def update_instruction(profile_id:int,data:InstructionIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.get(InstructionProfile,profile_id)
    if not item:raise HTTPException(404,detail="Instruction profile not found")
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.commit();db.refresh(item);return item
@app.delete("/api/v1/admin/instructions/{profile_id}",status_code=204)
def delete_instruction(profile_id:int,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.get(InstructionProfile,profile_id)
    if not item:raise HTTPException(404,detail="Instruction profile not found")
    db.delete(item);db.commit()

@app.post("/api/v1/admin/ai-control/preview")
def preview_ai_message(data: AIPreviewIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    profile = db.get(InstructionProfile, data.instruction_profile_id) if data.instruction_profile_id else db.query(InstructionProfile).filter_by(active=True).first()
    if not profile:
        raise HTTPException(422, detail="AI_INSTRUCTION_PROFILE_REQUIRED")
    evidence = []
    if data.website:
        evidence.append(f"Website recorded: {data.website}")
    if data.website_status and data.website_status.lower() != "unknown":
        evidence.append(f"Website status: {data.website_status}")
    context = data.previous_conversation.strip()
    if context:
        evidence.append(f"Previous conversation: {context[-1200:]}")
    draft = MessageComposerEngine().compose(
        profile=profile,
        business_name=data.business_name.strip() or "Unknown business",
        offer=profile.offer,
        service_summary=profile.services,
        cta=profile.cta,
        evidence=evidence,
        tone=profile.tone,
        niche=profile.niche,
        previous_conversation=context,
    )
    return {"mode": "TEST_SIMULATION", "subject": draft.subject, "body": draft.body, "profile_id": profile.id, "persisted": False}
@app.post("/api/v1/jobs",status_code=201)
def create_job(data:JobIn,db:Session=Depends(get_db)):return jobs.enqueue(db,data.job_type,data.payload,data.total)
@app.get("/api/v1/jobs")
def list_jobs(db:Session=Depends(get_db)):return db.query(Job).order_by(Job.id.desc()).limit(100).all()
@app.post("/api/v1/jobs/{job_id}/{action}")
def job_action(job_id:int,action:str,db:Session=Depends(get_db)):
    if action not in {"pause","resume","cancel","retry"}:raise HTTPException(404,detail="Unknown action")
    job=db.get(Job,job_id)
    if not job:raise HTTPException(404,detail="Job not found")
    try:return jobs.transition(db,job,action)
    except ValueError as exc:raise HTTPException(409,detail=str(exc)) from exc
@app.get("/api/v1/admin/voice-agent")
def get_voice(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    config=db.query(VoiceAgentConfig).first()
    if not config:
        return {"status":"NOT_CONFIGURED","name":"Local voice agent","base_url":"","health_path":"/health","call_path":"/calls","enabled":False}
    try:
        runtime_config = json.loads(config.config or "{}")
    except json.JSONDecodeError:
        runtime_config = {}
    return {"id": config.id, "name": config.name, "base_url": config.base_url, "health_path": config.health_path, "call_path": config.call_path, "config": runtime_config, "enabled": config.enabled, "status": LocalVoiceAgentProvider(config).status}
@app.put("/api/v1/admin/voice-agent")
def save_voice(data:VoiceIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    config=db.query(VoiceAgentConfig).first() or VoiceAgentConfig()
    for key,value in data.model_dump().items():
        setattr(config, key, json.dumps(value) if key == "config" else value)
    db.add(config);db.commit();db.refresh(config);return get_voice(db)


@app.post("/api/v1/admin/voice-agent/disconnect")
def disconnect_voice(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    config = db.query(VoiceAgentConfig).first()
    if not config:
        return {"status": "NOT_CONFIGURED"}
    config.enabled = False
    config.base_url = ""
    config.health_path = "/health"
    config.call_path = "/calls"
    db.add(config)
    db.commit()
    return {"status": "DISCONNECTED"}


@app.post("/api/v1/admin/voice-agent/test")
async def test_voice(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    config = db.query(VoiceAgentConfig).first()
    provider = LocalVoiceAgentProvider(config)
    if provider.status == "NOT_CONFIGURED":
        raise HTTPException(503, detail="VOICE_AGENT_NOT_CONFIGURED")
    try:
        result = await provider.health_check()
        return result
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, detail="VOICE_AGENT_OFFLINE") from exc
@app.post("/api/v1/intelligence/score")
def score(payload:dict):return IntelligenceEngine().score(payload.get("website_status"),bool(payload.get("phone")),bool(payload.get("website"))).__dict__
@app.get("/api/v1/admin/logs")
def list_logs(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()

def normalize_provider_name(provider: str) -> str:
    return str(provider or "").strip().upper().replace("-", "_")


def safe_integration(item:Integration, provider:str):
    return {"provider":provider,"status":item.status or "NOT_CONFIGURED","account_name":item.account_name or "","capabilities":json.loads(item.capabilities or "[]"),"enabled":bool(item.enabled),"last_error":item.last_error or "","last_verified":item.last_test_at,"configured":bool(item.secret_value)}


def integration_status(db: Session, provider: str) -> dict:
    item = db.query(Integration).filter_by(provider=provider).first()
    account_provider = "META" if provider in {"INSTAGRAM", "FACEBOOK"} else provider
    account = db.query(Account).filter_by(provider=account_provider).order_by(Account.id.desc()).first()
    result = safe_integration(item or Integration(provider=provider), provider)
    if account and account.status == "ACTIVE" and account.access_token_encrypted:
        capabilities = account_capabilities(account, provider)
        result.update({
            "status": "CONNECTED",
            "account_name": account.name or account.email,
            "configured": True,
            "enabled": True,
            "capabilities": result["capabilities"] or capabilities,
            "last_error": "",
        })
    return result


def account_capabilities(account: Account, channel: str | None = None) -> list[str]:
    """Return only capabilities backed by this account's stored configuration."""
    try:
        settings_data = json.loads(account.settings or "{}")
    except json.JSONDecodeError:
        settings_data = {}
    provider = (account.provider or "").upper()
    capabilities = ["profile"]
    if provider == "GMAIL":
        capabilities.append("email")
    elif provider == "META":
        if settings_data.get("phone_number_id"):
            capabilities.append("whatsapp_messaging")
        if settings_data.get("business_account_id"):
            capabilities.append("instagram_messaging")
        if settings_data.get("page_access_token"):
            capabilities.append("facebook_messaging")
    if channel:
        normalized = normalize_provider_name(channel)
        aliases = {"EMAIL": "email", "GMAIL": "email", "WHATSAPP": "whatsapp_messaging", "INSTAGRAM": "instagram_messaging", "FACEBOOK": "facebook_messaging"}
        required = aliases.get(normalized, normalized.lower() + "_messaging")
        return [required] if required in capabilities else []
    return capabilities


def sender_account(db: Session, channel: str, account_id: int | None) -> Account:
    if account_id is None:
        raise HTTPException(422, detail="SENDER_ACCOUNT_REQUIRED")
    account = db.get(Account, account_id)
    if not account or account.status != "ACTIVE" or not account.access_token_encrypted:
        raise HTTPException(422, detail="SENDER_ACCOUNT_NOT_CONNECTED")
    if account.token_expires_at and account.token_expires_at <= datetime.now(timezone.utc):
        if not account.refresh_token_encrypted:
            raise HTTPException(422, detail="SENDER_ACCOUNT_EXPIRED_RECONNECT_REQUIRED")
        try:
            refresh_token = secret_store.decrypt(account.refresh_token_encrypted)
            refreshed = oauth_service.refresh_tokens(account.provider, refresh_token)
            account.access_token_encrypted = secret_store.encrypt(str(refreshed["access_token"]))
            if refreshed.get("refresh_token"):
                account.refresh_token_encrypted = secret_store.encrypt(str(refreshed["refresh_token"]))
            if refreshed.get("expires_in") is not None:
                account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(refreshed["expires_in"]))
            account.status = "ACTIVE"
            db.commit()
        except (ValueError, KeyError, TypeError) as exc:
            account.status = "SUSPENDED"
            db.commit()
            raise HTTPException(422, detail="SENDER_ACCOUNT_REFRESH_FAILED_RECONNECT_REQUIRED") from exc
    if not account_capabilities(account, channel):
        raise HTTPException(422, detail=f"SENDER_ACCOUNT_CANNOT_SEND_{normalize_provider_name(channel)}")
    return account


def provider_for_account(channel: str, account: Account):
    provider_channel = normalize_provider_name(channel)
    token = secret_store.decrypt(account.access_token_encrypted)
    try:
        settings_data = json.loads(account.settings or "{}")
    except json.JSONDecodeError:
        settings_data = {}
    kwargs: dict[str, Any] = {}
    if provider_channel in {"EMAIL", "GMAIL"}:
        provider_channel = "GMAIL"
        kwargs["access_token"] = token
    elif provider_channel == "WHATSAPP":
        kwargs.update(token=token, phone_number_id=settings_data.get("phone_number_id", ""), business_account_id=settings_data.get("business_account_id", ""))
    elif provider_channel == "INSTAGRAM":
        kwargs.update(access_token=token, business_account_id=settings_data.get("business_account_id", ""))
    elif provider_channel == "FACEBOOK":
        kwargs["page_access_token"] = settings_data.get("page_access_token", token)
    return MessageProviderFactory.create(provider_channel, **kwargs)


def _contact_profile_settings(db: Session) -> dict[str, str]:
    settings = {}
    for key in [
        "contact.voice_phone",
        "contact.voice_phone_verified",
        "contact.whatsapp_phone",
        "contact.whatsapp_phone_verified",
        "contact.instagram_handle",
        "contact.facebook_handle",
        "contact.linkedin_url",
        "contact.threads_url",
        "contact.tiktok_handle",
        "contact.gmail_email",
        "contact.email_sender_name",
    ]:
        item = db.query(AdminSetting).filter_by(key=key).first()
        settings[key] = item.value if item else ""
    return settings


def _save_call_transcript(call_id: int, lead_id: int | None, caller_id: str, to_number: str, transcript: str, response_text: str) -> tuple[str, str]:
    transcript_dir = Path(__file__).resolve().parent.parent / "call_transcripts"
    transcript_dir.mkdir(exist_ok=True)
    safe_name = f"call_{call_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    text_path = transcript_dir / f"{safe_name}.txt"
    pdf_path = transcript_dir / f"{safe_name}.pdf"

    text_payload = "\n".join([
        "LeadPilot Voice Call Transcript",
        f"Call ID: {call_id}",
        f"Lead ID: {lead_id or 'N/A'}",
        f"Caller: {caller_id or 'N/A'}",
        f"Destination: {to_number or 'N/A'}",
        "",
        "Agent:",
        response_text,
        "",
        "Transcript:",
        transcript or "No transcript captured.",
    ])
    text_path.write_text(text_payload, encoding="utf-8")

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
        pdf.setTitle(f"LeadPilot call transcript {call_id}")
        pdf.setFont("Helvetica", 12)
        lines = text_payload.splitlines()
        y = 760
        for line in lines:
            if y < 40:
                pdf.showPage()
                y = 760
            pdf.drawString(50, y, line[:110])
            y -= 18
        pdf.save()
    except Exception:
        pdf_path = text_path

    return str(text_path), str(pdf_path)


@app.get("/api/v1/admin/contact-profile")
def get_contact_profile(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    profile = _contact_profile_settings(db)
    voice_phone = profile.get("contact.voice_phone", "")
    whatsapp_phone = profile.get("contact.whatsapp_phone", "")
    voice_verified = profile.get("contact.voice_phone_verified", "false") == "true"
    whatsapp_verified = profile.get("contact.whatsapp_phone_verified", "false") == "true"
    return {
        "phone_number": voice_phone or whatsapp_phone,
        "voice_phone": voice_phone,
        "voice_phone_status": "VERIFIED" if voice_verified else ("PENDING_PROVIDER_VERIFICATION" if voice_phone else "NOT_CONFIGURED"),
        "whatsapp_phone": whatsapp_phone,
        "whatsapp_phone_status": "VERIFIED" if whatsapp_verified else ("PENDING_PROVIDER_VERIFICATION" if whatsapp_phone else "NOT_CONFIGURED"),
        "instagram_handle": profile.get("contact.instagram_handle", ""),
        "facebook_handle": profile.get("contact.facebook_handle", ""),
        "linkedin_url": profile.get("contact.linkedin_url", ""),
        "threads_url": profile.get("contact.threads_url", ""),
        "tiktok_handle": profile.get("contact.tiktok_handle", ""),
        "gmail_email": profile.get("contact.gmail_email", ""),
        "email_sender_name": profile.get("contact.email_sender_name", ""),
    }


@app.put("/api/v1/admin/contact-profile")
def save_contact_profile(data: dict, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    shared_phone = str(data.get("phone_number", "") or "").strip()
    if shared_phone:
        data = {**data, "voice_phone": shared_phone, "whatsapp_phone": shared_phone}
    allowed = {
        "voice_phone": "contact.voice_phone",
        "whatsapp_phone": "contact.whatsapp_phone",
        "instagram_handle": "contact.instagram_handle",
        "facebook_handle": "contact.facebook_handle",
        "linkedin_url": "contact.linkedin_url",
        "threads_url": "contact.threads_url",
        "tiktok_handle": "contact.tiktok_handle",
        "gmail_email": "contact.gmail_email",
        "email_sender_name": "contact.email_sender_name",
    }

    for key, db_key in allowed.items():
        value = data.get(key, "")
        item = db.query(AdminSetting).filter_by(key=db_key).first() or AdminSetting(key=db_key)
        item.value = str(value or "").strip()
        db.add(item)
    for phone_key in ("voice_phone", "whatsapp_phone"):
        phone = str(data.get(phone_key, "") or "").strip()
        verified_key = f"contact.{phone_key}_verified"
        verified = db.query(AdminSetting).filter_by(key=verified_key).first() or AdminSetting(key=verified_key)
        if not phone or not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
            verified.value = "false"
        db.add(verified)
    db.commit()
    return get_contact_profile(db, admin)


def _outreach_profile(db: Session) -> dict[str, Any]:
    def read(key: str, default: Any):
        item = db.query(AdminSetting).filter_by(key=f"outreach.{key}").first()
        if not item or not item.value:
            return default
        try:
            return json.loads(item.value)
        except json.JSONDecodeError:
            return item.value

    return {
        "portfolio_urls": read("portfolio_urls", []),
        "reference_websites": read("reference_websites", []),
        "sender_name": read("sender_name", ""),
        "default_cta": read("default_cta", "Would you like a quick, no-pressure review?"),
    }


@app.get("/api/v1/admin/outreach-profile")
def get_outreach_profile(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return _outreach_profile(db)


@app.put("/api/v1/admin/outreach-profile")
def save_outreach_profile(data: OutreachProfileIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    values = data.model_dump()
    for key, value in values.items():
        item = db.query(AdminSetting).filter_by(key=f"outreach.{key}").first() or AdminSetting(key=f"outreach.{key}")
        item.value = json.dumps(value)
        item.protected = False
        db.add(item)
    db.commit()
    return _outreach_profile(db)


@app.post("/api/v1/admin/contact-profile/{phone_key}/verification-request")
def request_phone_verification(phone_key: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if phone_key not in {"voice_phone", "whatsapp_phone"}:
        raise HTTPException(404, detail="PHONE_PROFILE_NOT_FOUND")
    profile = _contact_profile_settings(db)
    phone = profile.get(f"contact.{phone_key}", "")
    if not re.fullmatch(r"\+[1-9]\d{7,14}", phone):
        raise HTTPException(422, detail="PHONE_MUST_USE_E164_FORMAT")
    code = f"{secrets.randbelow(1000000):06d}"
    challenge_key = f"verification_code:{phone_key}"
    challenge = db.query(AdminSetting).filter_by(key=challenge_key).first() or AdminSetting(key=challenge_key, protected=True)
    challenge.value = secret_store.encrypt(json.dumps({"phone": phone, "code": code, "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()}))
    challenge.protected = True
    db.add(challenge)
    db.commit()
    response = {"phone": phone, "status": "PENDING_PROVIDER_VERIFICATION", "message": "Verification code generated. Configure a production verification sender before exposing this flow."}
    if settings.development_mode:
        response["development_code"] = code
    return response


@app.post("/api/v1/admin/contact-profile/{phone_key}/verification-confirm")
def confirm_phone_verification(phone_key: str, data: PhoneVerificationIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    if phone_key not in {"voice_phone", "whatsapp_phone"}:
        raise HTTPException(404, detail="PHONE_PROFILE_NOT_FOUND")
    challenge = db.query(AdminSetting).filter_by(key=f"verification_code:{phone_key}").first()
    if not challenge or not challenge.value:
        raise HTTPException(409, detail="VERIFICATION_NOT_REQUESTED")
    try:
        payload = json.loads(secret_store.decrypt(challenge.value))
        expires_at = datetime.fromisoformat(payload["expires_at"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(409, detail="VERIFICATION_INVALID") from exc
    if expires_at <= datetime.now(timezone.utc) or not secrets.compare_digest(str(payload.get("code", "")), data.code):
        raise HTTPException(422, detail="VERIFICATION_CODE_INVALID")
    verified = db.query(AdminSetting).filter_by(key=f"contact.{phone_key}_verified").first() or AdminSetting(key=f"contact.{phone_key}_verified")
    verified.value = "true"
    db.add(verified)
    challenge.value = ""
    db.add(challenge)
    db.commit()
    return {"phone": payload["phone"], "status": "VERIFIED"}


def google_provider(db:Session) -> GooglePlacesProvider:
    item=db.query(Integration).filter_by(provider="GOOGLE_PLACES").first()
    secret = secret_store.decrypt(item.secret_value) if item and item.secret_value else ""
    return GooglePlacesProvider(secret) if secret else GooglePlacesProvider()


@app.post("/api/v1/admin/login")
def login_admin(data: dict, db: Session = Depends(get_db)):
    username = str(data.get("username", "")).strip() or settings.admin_username
    password = str(data.get("password", "")).strip() or settings.admin_password
    if username != settings.admin_username or password != settings.admin_password:
        raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")
    token = create_admin_token(username)
    return {"token": token, "role": "admin", "username": username, "expires_in_hours": 12}


@app.get("/api/v1/admin/me")
def admin_me(admin: dict = Depends(require_admin)):
    return {"username": admin.get("username", settings.admin_username), "role": admin.get("role", "admin")}


@app.get("/api/v1/admin/settings")
def list_admin_settings(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    settings_items = db.query(AdminSetting).order_by(AdminSetting.key.asc()).all()
    payload = []
    for item in settings_items:
        value = item.value if not item.protected else secret_store.mask(item.value)
        payload.append({"key": item.key, "value": value, "protected": item.protected})
    return payload


def _read_admin_theme(db: Session):
    try:
        db.execute(text("SELECT 1 FROM admin_settings LIMIT 1"))
    except Exception:
        AdminSetting.__table__.create(bind=db.bind, checkfirst=True)

    theme = db.query(AdminSetting).filter_by(key="ui.theme").first()
    reduced_motion = db.query(AdminSetting).filter_by(key="ui.reduced_motion").first()
    theme_name = (theme.value if theme and theme.value else "OBSIDIAN").upper()
    if theme_name not in {"OBSIDIAN", "AURORA"}:
        theme_name = "OBSIDIAN"
    reduced = str((reduced_motion.value if reduced_motion and reduced_motion.value else "false")).strip().lower() == "true"
    return {
        "theme": theme_name,
        "reduced_motion": reduced,
        "available_themes": ["OBSIDIAN", "AURORA"],
    }


@app.get("/api/v1/admin/theme")
def get_theme(db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    return _read_admin_theme(db)


@app.put("/api/v1/admin/theme")
def update_theme(data: ThemeIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    try:
        db.execute(text("SELECT 1 FROM admin_settings LIMIT 1"))
    except Exception:
        AdminSetting.__table__.create(bind=db.bind, checkfirst=True)

    theme_name = str(data.theme or "OBSIDIAN").upper().strip()
    if theme_name not in {"OBSIDIAN", "AURORA"}:
        raise HTTPException(status_code=422, detail="Theme must be OBSIDIAN or AURORA")

    theme_item = db.query(AdminSetting).filter_by(key="ui.theme").first() or AdminSetting(key="ui.theme")
    motion_item = db.query(AdminSetting).filter_by(key="ui.reduced_motion").first() or AdminSetting(key="ui.reduced_motion")
    theme_item.value = theme_name
    motion_item.value = "true" if bool(data.reduced_motion) else "false"
    db.add(theme_item)
    db.add(motion_item)
    db.commit()
    return _read_admin_theme(db)


@app.get("/api/v1/admin/overview")
def admin_overview(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    return {
        "leads": db.query(Lead).count(),
        "customers": db.query(Customer).count(),
        "projects": db.query(Project).count(),
        "campaigns": db.query(Campaign).count(),
        "jobs": db.query(Job).count(),
        "integrations_configured": db.query(Integration).filter(Integration.status == "CONNECTED").count(),
        "active_instruction_profiles": db.query(InstructionProfile).filter(InstructionProfile.active.is_(True)).count(),
        "voice_status": LocalVoiceAgentProvider(db.query(VoiceAgentConfig).first()).status,
    }


@app.get("/api/v1/readyz")
def readyz(db:Session=Depends(get_db)):
    return {"status": "READY", "database": "OK", "jobs": db.query(Job).count()}


@app.put("/api/v1/admin/settings/{key}")
def upsert_admin_setting(key: str, data: AdminSettingIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    item = db.query(AdminSetting).filter_by(key=key).first() or AdminSetting(key=key)
    item.protected = data.protected
    if data.protected:
        item.value = secret_store.encrypt(data.value)
    else:
        item.value = data.value
    db.add(item)
    db.commit()
    db.refresh(item)
    value = item.value if not item.protected else secret_store.mask(item.value)
    return {"key": item.key, "value": value, "protected": item.protected}


@app.get("/api/v1/admin/integrations")
def list_integrations(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    providers=["GOOGLE_PLACES","GMAIL","WHATSAPP","INSTAGRAM","FACEBOOK","LINKEDIN","X","TIKTOK","VOICE_AGENT","PAYMENTS"]
    return [integration_status(db, provider) for provider in providers]


@app.get("/api/v1/admin/accounts")
def list_accounts(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    providers=["GOOGLE_PLACES","GMAIL","WHATSAPP","INSTAGRAM","FACEBOOK","LINKEDIN","X","TIKTOK","VOICE_AGENT","PAYMENTS"]
    accounts = []
    for provider in providers:
        account_provider = "META" if provider in {"INSTAGRAM", "FACEBOOK"} else provider
        account = db.query(Account).filter_by(provider=account_provider).order_by(Account.id.desc()).first()
        if account and provider in {"WHATSAPP", "INSTAGRAM", "FACEBOOK"}:
            try:
                target = json.loads(account.settings or "{}").get("oauth_target")
            except json.JSONDecodeError:
                target = None
            if target != provider:
                account = None
        accounts.append({
            "provider": provider,
            "id": account.id if account else None,
            "status": account.status.value if account else "NOT_CONFIGURED",
            "account_name": account.name if account else "",
            "account_id": account.provider_user_id if account else "",
            "capabilities": account_capabilities(account, provider) if account else [],
            "connected_at": account.last_login_at if account else None,
            "last_error": "",
        })
    return accounts


@app.get("/api/v1/admin/oauth/config")
def oauth_config(admin: dict = Depends(require_admin)):
    expected_redirect = settings.frontend_origin.rstrip("/") + "/oauth/callback"
    return {
        "redirect_uri": expected_redirect,
        "providers": {
            "GMAIL": {"client_id": bool(settings.gmail_client_id), "client_secret": bool(settings.gmail_client_secret)},
            "META": {"app_id": bool(settings.meta_app_id), "app_secret": bool(settings.meta_app_secret), "api_version": settings.meta_api_version},
            "LINKEDIN": {"client_id": bool(settings.linkedin_client_id), "client_secret": bool(settings.linkedin_client_secret)},
            "X": {"client_id": bool(settings.x_client_id), "client_secret": bool(settings.x_client_secret)},
            "TIKTOK": {"client_id": bool(settings.tiktok_client_id), "client_secret": bool(settings.tiktok_client_secret)},
        },
    }


@app.put("/api/v1/admin/accounts/{provider}")
def configure_account(provider: str, data: AccountConfigureIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    provider_name = normalize_provider_name(provider)
    email = data.account_name.strip() or str(admin.get("username", settings.admin_username))
    account = db.query(Account).filter_by(email=email, provider=provider_name).first()
    if account is None:
        account = Account(email=email, name=data.account_name.strip() or email, provider=provider_name)
        db.add(account)
    account.name = data.account_name.strip() or account.name
    account.provider_user_id = data.provider_user_id.strip()
    if data.access_token:
        account.access_token_encrypted = secret_store.encrypt(data.access_token.strip())
    if data.refresh_token:
        account.refresh_token_encrypted = secret_store.encrypt(data.refresh_token.strip())
    if data.settings is not None:
        account.settings = json.dumps(data.settings)
    if data.token_expires_in is not None:
        account.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.token_expires_in)
    account.status = "ACTIVE" if account.access_token_encrypted else "PENDING_VERIFICATION"
    account.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "provider": account.provider, "name": account.name, "status": account.status.value}


@app.delete("/api/v1/admin/accounts/{provider}", status_code=204)
def disconnect_account(provider: str, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    provider_name = normalize_provider_name(provider)
    if provider_name in {"WHATSAPP", "INSTAGRAM", "FACEBOOK"}:
        provider_name = "META"
    accounts = db.query(Account).filter_by(provider=provider_name).all()
    for account in accounts:
        account.access_token_encrypted = ""
        account.refresh_token_encrypted = ""
        account.status = "INACTIVE"
    if accounts:
        db.commit()


@app.post("/api/v1/admin/oauth/begin")
def begin_oauth(data: OAuthBeginIn, admin: dict = Depends(require_admin)):
    try:
        expected_redirect = settings.frontend_origin.rstrip("/") + "/oauth/callback"
        if data.redirect_uri.rstrip("/") != expected_redirect.rstrip("/"):
            raise ValueError("OAUTH_REDIRECT_URI_MISMATCH")
        target = normalize_provider_name(data.target_provider or data.provider)
        extra_params = dict(data.extra_params or {})
        extra_params["leadpilot_target"] = target
        return oauth_service.begin_authorization(
            data.provider,
            data.redirect_uri,
            extra_scopes=data.extra_scopes,
            extra_params=extra_params,
        )
    except ValueError as exc:
        logger.warning("OAuth begin failed provider=%s reason=%s", data.provider, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/admin/oauth/callback")
def complete_oauth(data: OAuthCallbackIn, db: Session = Depends(get_db), admin: dict = Depends(require_admin)):
    stored = StateManager.validate(data.state)
    if stored is None:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_STATE")
    provider = str(stored.get("provider", ""))
    target_provider = normalize_provider_name(str(stored.get("target_provider") or provider))
    try:
        tokens = oauth_service.exchange_code(provider, data.code, data.state, validated_state=stored)
        user_id = str(admin.get("username", settings.admin_username))
        profile = {}
        try:
            profile = profile_fetcher.fetch(provider, str(tokens.get("access_token", "")))
        except (ValueError, httpx.HTTPError):
            profile = {}
        account_name = str(profile.get("name") or profile.get("displayName") or profile.get("email") or profile.get("username") or user_id)
        provider_user_id = str(profile.get("id") or "")
        if provider == "META" and target_provider == "WHATSAPP":
            graph_version = settings.meta_api_version.strip("/") or "v22.0"
            graph_url = f"https://graph.facebook.com/{graph_version}/me/businesses"
            with httpx.Client(timeout=settings.request_timeout) as client:
                headers = {"Authorization": f"Bearer {tokens.get('access_token', '')}"}
                verification = client.get(graph_url, headers=headers)
            if verification.status_code >= 400 or not verification.json().get("data"):
                raise ValueError("WHATSAPP_BUSINESS_ONBOARDING_REQUIRED: Meta did not return an authorized business account")
            business = verification.json()["data"][0]
            profile["business_id"] = str(business.get("id", ""))
            profile["business_name"] = str(business.get("name", ""))
            with httpx.Client(timeout=settings.request_timeout) as client:
                waba_response = client.get(f"https://graph.facebook.com/{graph_version}/{profile['business_id']}/owned_whatsapp_business_accounts", headers=headers)
                if waba_response.status_code >= 400 or not waba_response.json().get("data"):
                    raise ValueError("WHATSAPP_BUSINESS_ACCOUNT_REQUIRED: No WhatsApp Business Account was returned by Meta")
                waba = waba_response.json()["data"][0]
                phones = client.get(f"https://graph.facebook.com/{graph_version}/{waba['id']}/phone_numbers?fields=id,display_phone_number,verified_name,status", headers=headers)
            if phones.status_code >= 400 or not phones.json().get("data"):
                raise ValueError("WHATSAPP_PHONE_ONBOARDING_REQUIRED: Meta returned no verified WhatsApp phone number")
            phone = phones.json()["data"][0]
            profile.update({"waba_id": str(waba.get("id", "")), "phone_number_id": str(phone.get("id", "")), "display_phone_number": str(phone.get("display_phone_number", "")), "phone_status": str(phone.get("status", ""))})
        elif provider == "META" and target_provider == "INSTAGRAM":
            graph_version = settings.meta_api_version.strip("/") or "v22.0"
            with httpx.Client(timeout=settings.request_timeout) as client:
                response = client.get(f"https://graph.facebook.com/{graph_version}/me/accounts?fields=id,name,instagram_business_account", headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"})
            pages = response.json().get("data", []) if response.status_code < 400 else []
            instagram = next((page.get("instagram_business_account") for page in pages if page.get("instagram_business_account")), None)
            if not instagram:
                raise ValueError("INSTAGRAM_ACCOUNT_REQUIRED: Connect a supported Instagram professional account through Meta")
            profile["instagram_business_account_id"] = str(instagram.get("id", ""))
        elif provider == "META" and target_provider == "FACEBOOK":
            graph_version = settings.meta_api_version.strip("/") or "v22.0"
            with httpx.Client(timeout=settings.request_timeout) as client:
                response = client.get(f"https://graph.facebook.com/{graph_version}/me/accounts?fields=id,name", headers={"Authorization": f"Bearer {tokens.get('access_token', '')}"})
            pages = response.json().get("data", []) if response.status_code < 400 else []
            if not pages:
                raise ValueError("FACEBOOK_PAGE_REQUIRED: Meta did not return a Page managed by this account")
            profile["page_id"] = str(pages[0].get("id", ""))
            profile["page_name"] = str(pages[0].get("name", ""))
        settings_data = {
            "oauth_target": target_provider,
            "profile": profile,
            "phone_number_id": profile.get("phone_number_id", ""),
            "business_account_id": profile.get("waba_id") or profile.get("instagram_business_account_id", ""),
            "page_id": profile.get("page_id", ""),
        }
        oauth_service.store_tokens(user_id, provider, tokens, db=db, account_name=account_name, provider_user_id=provider_user_id)
        account = db.query(Account).filter_by(email=f"oauth:{provider.upper()}:{user_id}").first()
        if account is not None:
            account.settings = json.dumps(settings_data)
            db.commit()
    except ValueError as exc:
        logger.warning("OAuth callback failed provider=%s target=%s reason=%s", provider, target_provider, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "provider": target_provider,
        "status": "CONNECTED",
        "account": account_name,
        "provider_user_id": provider_user_id,
        "profile": profile,
        "token_expires_in": tokens.get("expires_in"),
    }


@app.post("/api/v1/admin/accounts/{provider}/default")
def set_default_account(provider:str, db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    provider_name = normalize_provider_name(provider)
    item = db.query(Integration).filter_by(provider=provider_name).first()
    if not item:
        raise HTTPException(404, detail="Account not configured")
    key = f"default_account_{provider_name}"
    setting = db.query(AdminSetting).filter_by(key=key).first() or AdminSetting(key=key)
    setting.value = str(item.id)
    setting.protected = False
    db.add(setting)
    db.commit()
    return {"provider": provider_name, "default_account_id": item.id, "status": item.status}


@app.get("/api/v1/admin/integrations/{provider}")
def get_integration(provider:str,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    name=normalize_provider_name(provider)
    return integration_status(db, name)

@app.put("/api/v1/admin/integrations/{provider}")
def configure_integration(provider:str,data:IntegrationConfigIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    name=normalize_provider_name(provider); item=db.query(Integration).filter_by(provider=name).first() or Integration(provider=name)
    item.account_name = (data.account_name or "").strip(); item.enabled = bool(data.enabled)
    if data.secret_value is not None:
        cleaned = data.secret_value.strip()
        item.secret_value = secret_store.encrypt(cleaned) if cleaned else ""
    item.status = "CONFIGURED" if item.enabled and bool(item.secret_value) else "NOT_CONFIGURED"; item.last_error=""
    db.add(item); db.commit(); db.refresh(item); return safe_integration(item,name)

@app.delete("/api/v1/admin/integrations/{provider}",status_code=204)
def disconnect_integration(provider:str,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.query(Integration).filter_by(provider=normalize_provider_name(provider)).first()
    if item: item.secret_value=""; item.account_name=""; item.enabled=False; item.status="NOT_CONFIGURED"; item.last_error=""; db.commit()

@app.post("/api/v1/admin/integrations/gmail/test")
async def test_gmail(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.query(Integration).filter_by(provider="GMAIL").first()
    if not item or not item.secret_value: raise HTTPException(503,detail="GMAIL_NOT_CONFIGURED")
    secret = secret_store.decrypt(item.secret_value)
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client: response=await client.get("https://gmail.googleapis.com/gmail/v1/users/me/profile",headers={"Authorization":"Bearer "+secret})
        if response.status_code in {401,403}: raise HTTPException(503,detail="GMAIL_AUTHENTICATION_FAILED")
        response.raise_for_status(); profile=response.json(); item.account_name=profile.get("emailAddress",item.account_name); item.status="CONNECTED"; item.capabilities=json.dumps(["email_send","email_profile"]); item.last_error=""; item.last_test_at=datetime.now(timezone.utc); db.commit(); return safe_integration(item,"GMAIL")
    except HTTPException: raise
    except Exception as exc: item.status="ERROR"; item.last_error="GMAIL_PROVIDER_ERROR"; db.commit(); raise HTTPException(502,detail="GMAIL_PROVIDER_ERROR") from exc

@app.post("/api/v1/email/send")
async def send_email(data:EmailSendIn,db:Session=Depends(get_db)):
    item=db.query(Integration).filter_by(provider="GMAIL").first()
    if not item or item.status!="CONNECTED": raise HTTPException(503,detail="GMAIL_NOT_CONNECTED")
    raw=f"To: {data.recipient}\r\nSubject: {data.subject}\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{data.content}"
    token = secret_store.decrypt(item.secret_value)
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client: response=await client.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},json={"raw":base64.urlsafe_b64encode(raw.encode()).decode()})
        if response.status_code in {401,403}: raise HTTPException(503,detail="GMAIL_AUTHENTICATION_FAILED")
        response.raise_for_status(); return {"status":"SENT","provider_reference":response.json().get("id","")}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(502,detail="GMAIL_SEND_FAILED") from exc

@app.post("/api/v1/admin/integrations/{provider}/test")
async def test_social_provider(provider:str,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    name=normalize_provider_name(provider)
    if name in {"GOOGLE_PLACES","GMAIL"}: raise HTTPException(404,detail="Use the provider-specific test route")
    item=db.query(Integration).filter_by(provider=name).first()
    if not item or not item.secret_value: raise HTTPException(503,detail=f"{name}_NOT_CONFIGURED")
    item.status="CAPABILITY_UNAVAILABLE"; item.last_error="Official provider verification requires OAuth onboarding and approved capabilities"; item.last_test_at=datetime.now(timezone.utc); db.commit()
    raise HTTPException(503,detail="CAPABILITY_UNAVAILABLE")
@app.get("/api/v1/admin/integrations/google-places")
def google_status(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.query(Integration).filter_by(provider="GOOGLE_PLACES").first()
    if item and item.secret_value: return safe_integration(item,"GOOGLE_PLACES")
    return {"provider":"GOOGLE_PLACES","status":"CONFIGURED" if GooglePlacesProvider().configured() else "NOT_CONFIGURED","account_name":"","capabilities":[],"enabled":False,"last_error":"","last_verified":None,"configured":GooglePlacesProvider().configured()}

@app.put("/api/v1/admin/integrations/google-places")
def configure_google(data:IntegrationConfigIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)): return configure_integration("GOOGLE_PLACES",data,db,admin)

@app.delete("/api/v1/admin/integrations/google-places",status_code=204)
def remove_google(db:Session=Depends(get_db), admin: dict = Depends(require_admin)): return disconnect_integration("GOOGLE_PLACES",db,admin)
@app.post("/api/v1/admin/integrations/google-places/test")
async def test_google(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.query(Integration).filter_by(provider="GOOGLE_PLACES").first()
    try:
        await google_provider(db).search("restaurant",1)
        if item: item.status="CONNECTED"; item.capabilities=json.dumps(["place_search","place_details"]); item.last_error=""; item.last_test_at=datetime.now(timezone.utc); db.commit()
        return google_status(db)
    except GooglePlacesError as exc: raise HTTPException(503,detail=str(exc)) from exc
    except Exception as exc: raise HTTPException(502,detail="GOOGLE_ERROR") from exc
@app.post("/api/v1/leads/discover",status_code=201)
async def discover(data:DiscoveryIn,db:Session=Depends(get_db)):
    try: places=await google_provider(db).search(" ".join(filter(None,[data.niche,data.keywords,data.location])),data.limit)
    except GooglePlacesError as exc:raise HTTPException(503,detail=str(exc)) from exc
    created=0
    for place in places:
        place_id=place.get("id")
        if not place_id or db.query(Business).filter_by(google_place_id=place_id).first(): continue
        normalized=normalize_place(place)
        if not normalized.place_id or not normalized.name: continue
        business=Business(google_place_id=normalized.place_id,business_name=normalized.name,address=normalized.address,locality=normalized.locality,city=normalized.city,region=normalized.region,country=normalized.country,website=normalized.website,phone=normalized.phone,category=normalized.category,categories=json.dumps(normalized.categories),latitude=str(normalized.latitude) if normalized.latitude is not None else None,longitude=str(normalized.longitude) if normalized.longitude is not None else None,rating=str(normalized.rating) if normalized.rating is not None else None,review_count=normalized.review_count,business_status=normalized.business_status,google_maps_url=normalized.maps_url,contact_status="CONTACTABLE")
        db.add(business);db.flush(); insight=IntelligenceEngine().score(None,bool(business.phone),bool(business.website));db.add(Lead(business_id=business.id,score=insight.score,grade=insight.classification,score_reasons=json.dumps(insight.reasons)));created+=1
    db.commit();return {"received":len(places),"created":created,"duplicates":len(places)-created}
@app.get("/api/v1/leads")
def list_leads(db:Session=Depends(get_db)):
    return [serialize_lead(lead, db) for lead in db.query(Lead).order_by(Lead.id.desc()).limit(100).all()]

def serialize_lead(lead:Lead, db:Session):
    business=lead.business
    return {"id":lead.id,"business":{"id":business.id,"name":business.business_name,"category":business.category,"categories":json.loads(business.categories or "[]"),"location":{"address":business.address,"locality":business.locality,"city":business.city,"region":business.region,"country":business.country,"latitude":business.latitude,"longitude":business.longitude},"contact":{"phone":business.phone},"website":business.website,"google":{"place_id":business.google_place_id,"maps_url":business.google_maps_url,"rating":business.rating,"review_count":business.review_count,"business_status":business.business_status},"social_profiles":[{"platform":item.platform,"profile_url":item.profile_url,"username":item.username,"source":item.source,"status":item.status} for item in db.query(BusinessSocialProfile).filter_by(business_id=business.id,status="STORED").all()]},"lifecycle":lead.lifecycle,"score":{"score":lead.score,"grade":lead.grade,"reasons":json.loads(lead.score_reasons or "[]")}}

@app.get("/api/v1/leads/{lead_id}")
def get_lead(lead_id:int,db:Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,detail="Lead not found")
    return serialize_lead(lead,db)

@app.post("/api/v1/businesses/{business_id}/social-profiles",status_code=201)
def add_social_profile(business_id:int,data:SocialProfileIn,db:Session=Depends(get_db)):
    from urllib.parse import urlparse
    parsed=urlparse(data.profile_url)
    if parsed.scheme.lower() != "https" or not parsed.netloc: raise HTTPException(422,detail="Only valid HTTPS social URLs are allowed")
    platform=data.platform.upper()
    if platform not in {"INSTAGRAM","FACEBOOK","LINKEDIN","X","TIKTOK","WHATSAPP"}: raise HTTPException(422,detail="Unsupported social platform")
    if db.query(BusinessSocialProfile).filter_by(business_id=business_id,platform=platform,profile_url=data.profile_url).first(): raise HTTPException(409,detail="Social profile already exists")
    if not db.get(Business,business_id): raise HTTPException(404,detail="Business not found")
    item=BusinessSocialProfile(business_id=business_id,platform=platform,profile_url=data.profile_url,username=data.username,source=data.source,status="STORED")
    db.add(item);db.commit();db.refresh(item);return item

@app.patch("/api/v1/leads/{lead_id}")
def update_lead(lead_id:int,data:StatusIn,db:Session=Depends(get_db)):
    allowed={"PROSPECT","CONTACTED","RESPONDED","INTERESTED","QUALIFIED","CUSTOMER","PROJECT","COMPLETED","OPTED_OUT"}
    if data.status not in allowed: raise HTTPException(422,detail="Unsupported lead status")
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,detail="Lead not found")
    lead.lifecycle=data.status; db.add(TimelineEvent(lead_id=lead.id,event_type="STATUS_CHANGED",detail=data.status)); db.commit()
    return {"id":lead.id,"status":lead.lifecycle}

@app.get("/api/v1/dashboard/metrics")
def dashboard_metrics(db:Session=Depends(get_db)):
    return {"leads":db.query(Lead).count(),"websites":db.query(Business).filter(Business.website.is_not(None),Business.website!="").count(),"qualified":db.query(Lead).filter(Lead.lifecycle=="QUALIFIED").count(),"contacted":db.query(Lead).filter(Lead.lifecycle=="CONTACTED").count(),"customers":db.query(Customer).count(),"projects":db.query(Project).count(),"campaigns":db.query(Campaign).count(),"queued":db.query(Message).filter(Message.status=="QUEUED").count(),"sent":db.query(Message).filter(Message.status=="SENT").count(),"failed":db.query(Message).filter(Message.status=="FAILED").count(),"active_jobs":db.query(Job).filter(Job.status.in_(["PENDING","RUNNING","PAUSED"])).count()}

@app.get("/api/v1/customers")
def list_customers(db:Session=Depends(get_db)):
    return [{"id":item.id,"lead_id":item.lead_id,"business":db.get(Business,item.business_id).business_name,"status":item.status,"notes":item.notes} for item in db.query(Customer).order_by(Customer.id.desc()).all()]


@app.get("/api/v1/calls")
def list_calls(db:Session=Depends(get_db)):
    return db.query(Call).order_by(Call.id.desc()).limit(100).all()

@app.get("/api/v1/communication-history")
def communication_history(db: Session = Depends(get_db)):
    messages = db.query(OutboundMessage).order_by(OutboundMessage.id.desc()).limit(100).all()
    calls = db.query(Call).order_by(Call.id.desc()).limit(100).all()
    history = []
    for message in messages:
        account = db.get(Account, message.account_id) if message.account_id else None
        history.append({"type": "MESSAGE", "id": message.id, "lead_id": message.lead_id, "channel": message.channel, "sender_account_id": message.account_id, "sender": account.name if account else "", "provider_message_id": message.provider_message_id, "status": message.status.value if hasattr(message.status, "value") else message.status, "recipient": message.recipient, "timestamp": message.sent_at or message.created_at, "error": message.error})
    for call in calls:
        history.append({"type": "CALL", "id": call.id, "lead_id": call.lead_id, "channel": "PHONE", "sender_account_id": None, "sender": call.from_number, "provider_message_id": call.provider_reference, "status": call.status.value if hasattr(call.status, "value") else call.status, "recipient": call.to_number, "timestamp": call.started_at or call.created_at, "outcome": call.result, "error": call.error, "duration_seconds": call.duration_seconds})
    return sorted(history, key=lambda item: str(item.get("timestamp") or ""), reverse=True)


@app.post("/api/v1/leads/{lead_id}/call", status_code=201)
async def start_call(lead_id:int, data:CallStartIn, db:Session=Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Lead not found")
    config = db.query(VoiceAgentConfig).first()
    provider = LocalVoiceAgentProvider(config)
    contact_profile = _contact_profile_settings(db)
    caller_id = str(data.caller_id or contact_profile.get("contact.voice_phone", "")).strip()
    to_number = str(data.to_number or contact_profile.get("contact.voice_phone", "")).strip()

    if not caller_id and not to_number and provider.status == "NOT_CONFIGURED":
        raise HTTPException(503, detail="VOICE_AGENT_NOT_CONFIGURED")

    item = Call(
        lead_id=lead_id,
        customer_id=None,
        status="QUEUED",
        provider_reference=data.agent_name or config.name if config else "local_voice_agent",
        result="{}",
        error="",
        from_number=caller_id,
        to_number=to_number,
    )
    db.add(item); db.flush()
    try:
        voice_config = {}
        if config and config.config:
            try:
                voice_config = json.loads(config.config)
            except json.JSONDecodeError:
                voice_config = {}
        payload = await provider.start_call(lead_id, caller_id, to_number=to_number, context=voice_config)
        item.status = "CONNECTED"
        item.result = json.dumps(payload)
        item.provider_reference = str(payload.get("provider_reference", item.provider_reference))
        item.from_number = caller_id
        item.to_number = to_number
        item.provider_data = json.dumps(payload)
        item.recording_url = str(payload.get("recording_url") or payload.get("recordingUrl") or "")
        item.transcript = str(payload.get("transcript") or "")
        item.started_at = datetime.now(timezone.utc)
        lead.lifecycle = "CALLED"
        db.add(TimelineEvent(lead_id=lead.id, event_type="CALL_STARTED", detail=f"Caller: {caller_id or 'local'} -> To: {to_number or 'local'}"))
        db.commit(); db.refresh(item)
        return item
    except (httpx.HTTPError, ValueError) as exc:
        item.status = "FAILED"
        item.error = str(exc)
        db.add(TimelineEvent(lead_id=lead.id, event_type="CALL_FAILED", detail=str(exc)))
        db.commit(); db.refresh(item)
        raise HTTPException(503, detail="VOICE_AGENT_OFFLINE") from exc


@app.post("/api/v1/webhooks/voice/{call_id}")
async def voice_call_webhook(call_id: int, request: Request, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("X-LeadPilot-Signature", "")
    if settings.webhook_signing_secret:
        expected = "sha256=" + hmac.new(settings.webhook_signing_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="INVALID_WEBHOOK_SIGNATURE")
    elif not settings.development_mode:
        raise HTTPException(status_code=503, detail="WEBHOOK_SIGNING_SECRET_NOT_CONFIGURED")
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="INVALID_WEBHOOK_JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="WEBHOOK_PAYLOAD_MUST_BE_OBJECT")
    item = db.get(Call, call_id)
    if not item:
        raise HTTPException(404, detail="CALL_NOT_FOUND")
    item.provider_data = json.dumps(payload)
    status = str(payload.get("status") or "COMPLETED").upper()
    item.status = CallStatus(status) if status in {member.value for member in CallStatus} else CallStatus.COMPLETED
    item.recording_url = str(payload.get("recording_url") or payload.get("recordingUrl") or item.recording_url or "")
    item.transcript = str(payload.get("transcript") or item.transcript or "")
    item.duration_seconds = int(payload.get("duration_seconds") or payload.get("duration") or item.duration_seconds or 0)
    item.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/v1/leads/{lead_id}/customer",status_code=201)
def convert_customer(lead_id:int,data:CustomerIn,db:Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,detail="Lead not found")
    customer=db.query(Customer).filter_by(lead_id=lead_id).first()
    if customer: return customer
    customer=Customer(lead_id=lead.id,business_id=lead.business_id,notes=data.notes); lead.lifecycle="CUSTOMER"; db.add(customer); db.flush(); db.add(TimelineEvent(lead_id=lead.id,customer_id=customer.id,event_type="CUSTOMER_CREATED",detail="Lead converted to customer")); db.commit(); db.refresh(customer); return customer

@app.get("/api/v1/customers/{customer_id}/projects")
def list_projects(customer_id:int,db:Session=Depends(get_db)): return db.query(Project).filter_by(customer_id=customer_id).order_by(Project.id.desc()).all()

@app.post("/api/v1/customers/{customer_id}/projects",status_code=201)
def create_project(customer_id:int,data:ProjectIn,db:Session=Depends(get_db)):
    if not db.get(Customer,customer_id): raise HTTPException(404,detail="Customer not found")
    project=Project(customer_id=customer_id,**data.model_dump()); db.add(project); db.add(TimelineEvent(customer_id=customer_id,event_type="PROJECT_CREATED",detail=data.name)); db.commit(); db.refresh(project); return project

@app.patch("/api/v1/projects/{project_id}")
def update_project(project_id:int,data:ProjectIn,db:Session=Depends(get_db)):
    project=db.get(Project,project_id)
    if not project: raise HTTPException(404,detail="Project not found")
    for key,value in data.model_dump().items(): setattr(project,key,value)
    db.commit(); db.refresh(project); return project

@app.post("/api/v1/leads/{lead_id}/notes",status_code=201)
def add_note(lead_id:int,data:NoteIn,db:Session=Depends(get_db)):
    if not db.get(Lead,lead_id): raise HTTPException(404,detail="Lead not found")
    item=Note(lead_id=lead_id,content=data.content); db.add(item); db.add(TimelineEvent(lead_id=lead_id,event_type="NOTE_ADDED",detail=data.content)); db.commit(); db.refresh(item); return item

@app.get("/api/v1/leads/{lead_id}/timeline")
def lead_timeline(lead_id:int,db:Session=Depends(get_db)): return db.query(TimelineEvent).filter_by(lead_id=lead_id).order_by(TimelineEvent.id.desc()).all()

@app.post("/api/v1/customers/{customer_id}/payments",status_code=201)
def add_payment(customer_id:int,data:PaymentIn,db:Session=Depends(get_db)):
    if not db.get(Customer,customer_id): raise HTTPException(404,detail="Customer not found")
    payment=Payment(customer_id=customer_id,**data.model_dump()); db.add(payment); db.commit(); db.refresh(payment); return payment

@app.get("/api/v1/campaigns")
def list_campaigns(db:Session=Depends(get_db)): return db.query(Campaign).order_by(Campaign.id.desc()).all()


@app.get("/api/v1/campaigns/{campaign_id}/items")
def campaign_items(campaign_id:int, db:Session=Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    items = db.query(CampaignItem).filter_by(campaign_id=campaign_id).order_by(CampaignItem.id.desc()).all()
    return [{"id": item.id, "lead_id": item.lead_id, "message_id": item.message_id, "status": item.status} for item in items]


@app.post("/api/v1/campaigns",status_code=201)
def create_campaign(data:CampaignIn,db:Session=Depends(get_db)):
    account = sender_account(db, data.channel, data.sender_account_id)
    if not data.lead_ids: raise HTTPException(422,detail="Select at least one lead")
    campaign=Campaign(name=data.name,channel=data.channel,sender_account_id=account.id,sender_account=account.name,instruction_profile_id=data.instruction_profile_id); db.add(campaign); db.flush()
    for lead_id in data.lead_ids:
        if db.get(Lead,lead_id): db.add(CampaignItem(campaign_id=campaign.id,lead_id=lead_id))
    db.commit(); db.refresh(campaign); return campaign


@app.post("/api/v1/campaigns/{campaign_id}/launch")
def launch_campaign(campaign_id:int, db:Session=Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    campaign.status = "QUEUED"
    db.add(campaign)
    db.commit()
    return {"id": campaign.id, "status": campaign.status, "items": db.query(CampaignItem).filter_by(campaign_id=campaign_id).count()}


def _campaign_draft(lead: Lead, profile: InstructionProfile | None, service: ServiceProfile | None, outreach: dict[str, Any], db: Session):
    audit = db.query(WebsiteAudit).filter_by(business_id=lead.business_id).first()
    has_website = bool(lead.business.website)
    evidence = json.loads(audit.evidence).get("reasons", []) if audit else json.loads(lead.score_reasons or "[]")
    if has_website:
        evidence.append(f"Website reviewed: {lead.business.website}")
        opening_context = "The outreach references the recipient's existing website and its visible improvement opportunities."
    else:
        evidence.append("No website is recorded for this business")
        opening_context = "The outreach offers a first website conversation because no website is recorded."
    links = list(outreach.get("portfolio_urls", [])) + list(outreach.get("reference_websites", []))
    if links:
        evidence.append("Portfolio and reference links: " + ", ".join(str(link) for link in links))
    previous_messages = db.query(OutboundMessage).filter(OutboundMessage.lead_id == lead.id).order_by(OutboundMessage.id.desc()).limit(5).all()
    previous_conversation = "\n".join(
        f"{item.channel} ({item.status.value if hasattr(item.status, 'value') else item.status}): {item.body}"
        for item in reversed(previous_messages)
    )
    draft = MessageComposerEngine().compose(
        profile=profile,
        business_name=lead.business.business_name,
        offer=profile.offer if profile else service.offer if service else "",
        service_summary=(service.services if service else "") + " " + opening_context,
        cta=profile.cta if profile else outreach.get("default_cta", "Would you like a quick, no-pressure review?"),
        evidence=evidence,
        tone=profile.tone if profile else service.preferred_tone if service else "Professional",
        niche=profile.niche if profile else lead.business.category or "local business",
        previous_conversation=previous_conversation,
    )
    return draft


@app.post("/api/v1/campaigns/{campaign_id}/prepare")
def prepare_campaign(campaign_id: int, data: CampaignPrepareIn, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    if not data.lead_ids:
        raise HTTPException(422, detail="Select at least one lead")
    selected = set(data.lead_ids)
    items = db.query(CampaignItem).filter_by(campaign_id=campaign_id).all()
    if not selected.issubset({item.lead_id for item in items}):
        raise HTTPException(422, detail="Selected lead is not part of this campaign")
    profile = db.get(InstructionProfile, campaign.instruction_profile_id) if campaign.instruction_profile_id else db.query(InstructionProfile).filter_by(active=True).first()
    service = db.query(ServiceProfile).first()
    outreach = _outreach_profile(db)
    previews = []
    for item in items:
        if selected and item.lead_id not in selected:
            continue
        if item.status in {"SENT", "DELIVERED"}:
            continue
        lead = db.get(Lead, item.lead_id)
        if not lead:
            continue
        draft = _campaign_draft(lead, profile, service, outreach, db)
        previews.append({"lead_id": lead.id, "business_name": lead.business.business_name, "website": lead.business.website, "recipient": lead.business.phone or "", "subject": draft.subject, "body": draft.body, "status": item.status})
        item.status = "PREPARED"
    db.commit()
    return {"campaign_id": campaign_id, "count": len(previews), "previews": previews, "send_once_guard": True}


@app.post("/api/v1/campaigns/{campaign_id}/send-selected")
async def send_selected_campaign(campaign_id: int, data: CampaignSendIn, db: Session = Depends(get_db)):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, detail="Campaign not found")
    channel = (data.channel or campaign.channel).strip().upper()
    profile = db.get(InstructionProfile, campaign.instruction_profile_id) if campaign.instruction_profile_id else db.query(InstructionProfile).filter_by(active=True).first()
    service_profile = db.query(ServiceProfile).first()
    outreach = _outreach_profile(db)
    account = sender_account(db, channel, data.account_id or campaign.sender_account_id)
    provider = provider_for_account(channel, account)
    service = OutboundMessageService(db)
    selected = set(data.lead_ids)
    campaign_lead_ids = {item.lead_id for item in db.query(CampaignItem).filter_by(campaign_id=campaign_id).all()}
    if not selected.issubset(campaign_lead_ids):
        raise HTTPException(422, detail="Selected lead is not part of this campaign")
    results = []
    for item in db.query(CampaignItem).filter_by(campaign_id=campaign_id).all():
        if item.lead_id not in selected or item.status in {"SENT", "DELIVERED"}:
            continue
        lead = db.get(Lead, item.lead_id)
        if not lead or not lead.business.phone:
            results.append({"lead_id": item.lead_id, "status": "SKIPPED", "reason": "NO_RECIPIENT"})
            continue
        draft = _campaign_draft(lead, profile, service_profile, outreach, db)
        outbound, created = service.get_or_create(
            idempotency_key=f"campaign:{campaign_id}:lead:{lead.id}:{channel}",
            channel=channel,
            body=draft.body,
            recipient=lead.business.phone,
            subject=draft.subject,
            lead_id=lead.id,
            campaign_id=campaign_id,
            account_id=account.id,
        )
        if created:
            outbound = await service.send_once(provider, message=outbound, context={"subject": draft.subject})
        item.status = "SENT" if outbound.status in {OutboundMessageStatus.SENT, OutboundMessageStatus.DELIVERED} else "FAILED"
        results.append({"lead_id": lead.id, "status": item.status, "error": outbound.error})
    db.commit()
    return {"campaign_id": campaign_id, "channel": channel, "results": results, "send_once_guard": True}


@app.patch("/api/v1/campaigns/{campaign_id}")
def update_campaign(campaign_id:int,data:StatusIn,db:Session=Depends(get_db)):
    campaign=db.get(Campaign,campaign_id)
    if not campaign: raise HTTPException(404,detail="Campaign not found")
    if data.status not in {"DRAFT","QUEUED","RUNNING","PAUSED","CANCELLED","COMPLETED"}: raise HTTPException(422,detail="Unsupported campaign status")
    campaign.status=data.status; db.commit(); db.refresh(campaign); return campaign
@app.post("/api/v1/businesses/{business_id}/audit")
async def save_audit(business_id:int,db:Session=Depends(get_db)):
    business=db.get(Business,business_id)
    if not business:raise HTTPException(404,detail="Business not found")
    if not business.website: result={"classification":"NO_WEBSITE","reasons":["No website is recorded"]}
    else:
        try:result=await audit_website(business.website)
        except Exception:result={"classification":"UNREACHABLE","reasons":["Website could not be reached"]}
    record=db.query(WebsiteAudit).filter_by(business_id=business_id).first() or WebsiteAudit(business_id=business_id)
    record.status=result["classification"];record.evidence=json.dumps(result);db.add(record);db.commit();return result
@app.get("/api/v1/admin/service-profile")
def get_service_profile(db:Session=Depends(get_db), admin: dict = Depends(require_admin)):return db.query(ServiceProfile).first() or {}
@app.put("/api/v1/admin/service-profile")
def save_service_profile(data:ServiceIn,db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    item=db.query(ServiceProfile).first() or ServiceProfile()
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.add(item);db.commit();db.refresh(item);return item
@app.get("/api/v1/admin/instructions/{profile_id}/test")
def test_instruction_profile(profile_id:int, db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    profile = db.get(InstructionProfile, profile_id)
    if not profile: raise HTTPException(404, detail="Instruction profile not found")
    composer = MessageComposerEngine()
    draft = composer.compose(
        profile=profile,
        business_name="Sample Business",
        offer=profile.offer or "Conversion-focused local outreach",
        service_summary=profile.services or "Website + conversion support",
        cta=profile.cta or "Book a quick strategy call",
        evidence=["Public business profile reviewed", "Website information available"],
        tone=profile.tone,
        niche=profile.niche,
    )
    return {"profile_id": profile.id, "subject": draft.subject, "body": draft.body, "status": "READY"}


@app.post("/api/v1/admin/instructions/{profile_id}/activate")
def activate_instruction_profile(profile_id:int, db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    profile = db.get(InstructionProfile, profile_id)
    if not profile: raise HTTPException(404, detail="Instruction profile not found")
    for row in db.query(InstructionProfile).all():
        row.active = row.id == profile_id
    db.commit()
    profile.active = True
    db.commit()
    return {"id": profile.id, "active": True, "name": profile.name}


@app.post("/api/v1/admin/instructions/{profile_id}/duplicate")
def duplicate_instruction_profile(profile_id:int, db:Session=Depends(get_db), admin: dict = Depends(require_admin)):
    profile = db.get(InstructionProfile, profile_id)
    if not profile: raise HTTPException(404, detail="Instruction profile not found")
    clone = InstructionProfile(
        name=f"{profile.name} Copy",
        niche=profile.niche,
        language=profile.language,
        tone=profile.tone,
        offer=profile.offer,
        services=profile.services,
        cta=profile.cta,
        rules=profile.rules,
        do_not_say=profile.do_not_say,
        personalization_rules=profile.personalization_rules,
        additional_instructions=profile.additional_instructions,
        active=False,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone


@app.post("/api/v1/leads/{lead_id}/messages",status_code=201)
def create_draft(lead_id:int,data:DraftIn,db:Session=Depends(get_db)):
    lead=db.get(Lead,lead_id)
    if not lead:raise HTTPException(404,detail="Lead not found")
    profile=db.get(InstructionProfile,data.instruction_profile_id) if data.instruction_profile_id else db.query(InstructionProfile).filter_by(active=True).first()
    service=db.query(ServiceProfile).first(); audit=db.query(WebsiteAudit).filter_by(business_id=lead.business_id).first()
    evidence=json.loads(audit.evidence).get("reasons",[]) if audit else json.loads(lead.score_reasons)
    service_summary = service.services if service else ""
    instruction = " ".join(filter(None,[service.company_name if service else "",service.description if service else "",service.services if service else "",service.offer if service else "",service.cta if service else "",service.preferred_tone if service else "",service.additional_instructions if service else "",profile.offer if profile else "",profile.cta if profile else "",profile.additional_instructions if profile else ""]))
    composer = MessageComposerEngine()
    previous_messages = db.query(OutboundMessage).filter(OutboundMessage.lead_id == lead.id).order_by(OutboundMessage.id.desc()).limit(5).all()
    previous_conversation = "\n".join(item.body for item in reversed(previous_messages))
    draft = composer.compose(
        profile=profile,
        business_name=lead.business.business_name,
        offer=profile.offer if profile else service.offer if service else "",
        service_summary=service_summary,
        cta=profile.cta if profile else service.cta if service else "Book a quick strategy call",
        evidence=evidence,
        tone=profile.tone if profile else service.preferred_tone if service else "Professional",
        niche=profile.niche if profile else "",
        previous_conversation=previous_conversation,
    )
    content = draft.body
    message=Message(lead_id=lead.id,instruction_profile_id=profile.id if profile else None,channel=data.channel,recipient=data.recipient,subject=draft.subject,content=content,status="DRAFT")
    db.add(message);db.commit();db.refresh(message);return message
@app.post("/api/v1/messages/{message_id}/approve")
def approve_message(message_id:int,db:Session=Depends(get_db)):
    message=db.get(Message,message_id)
    if not message:raise HTTPException(404,detail="Message not found")
    if message.status!="DRAFT":raise HTTPException(409,detail="Only drafts can be approved")
    message.status="APPROVED";db.commit();db.refresh(message);return message


@app.post("/api/v1/messages/send", status_code=201)
async def send_message(data: MessageSendIn, db: Session = Depends(get_db)):
    """Deliver a message through a Python provider and persist the complete attempt."""
    channel = data.channel.strip().upper()
    account = sender_account(db, channel, data.account_id)
    try:
        provider = provider_for_account(channel, account)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

    service = OutboundMessageService(db)
    message, created = service.get_or_create(
        idempotency_key=data.idempotency_key,
        channel=channel,
        body=data.body,
        recipient=data.recipient,
        subject=data.subject,
        lead_id=data.lead_id,
        campaign_id=data.campaign_id,
        account_id=account.id,
    )
    if created:
        message = await service.send_once(
            provider,
            message=message,
            context={"subject": data.subject},
        )
    return {
        "id": message.id,
        "channel": message.channel,
        "recipient": message.recipient,
        "status": message.status.value if hasattr(message.status, "value") else message.status,
        "provider_message_id": message.provider_message_id,
        "error": message.error,
        "idempotent_replay": not created,
    }


@app.post("/api/v1/voice/agent/respond")
async def voice_agent_respond(data: VoiceAgentTurnIn, db: Session = Depends(get_db)):
    """Run one local conversation turn using the saved voice instructions."""
    conversation_id = data.conversation_id or "default"
    config = db.query(VoiceAgentConfig).first()
    voice_settings = {}
    if config and config.config:
        try:
            voice_settings = json.loads(config.config)
        except json.JSONDecodeError:
            voice_settings = {}
    brain = voice_brains.get(conversation_id)
    if brain is None:
        brain = RuleBrain(
            system_instructions=str(voice_settings.get("system_instructions", "")),
            portfolio=str(voice_settings.get("portfolio", "")),
            pricing_rules=str(voice_settings.get("pricing_rules", "")),
            conversation_context=str(voice_settings.get("conversation_context", "")),
        )
        voice_brains[conversation_id] = brain
    response_text = await brain.respond(data.text)
    return {
        "conversation_id": conversation_id,
        "transcript": data.text,
        "response_text": response_text,
        "engine": "LOCAL_RULE_BRAIN_WITH_SAVED_INSTRUCTIONS",
        "instructions_applied": bool(voice_settings),
        "status": "READY",
    }


@app.post("/api/v1/leads/{lead_id}/personalize",status_code=201)
def personalize(lead_id:int,data:DraftIn,db:Session=Depends(get_db)):
    """Explicit traceable pipeline: all returned context is persisted application data."""
    message=create_draft(lead_id,data,db); lead=db.get(Lead,lead_id); profile=db.get(InstructionProfile,message.instruction_profile_id) if message.instruction_profile_id else None
    audit=db.query(WebsiteAudit).filter_by(business_id=lead.business_id).first(); service=db.query(ServiceProfile).first()
    return {"message":message,"pipeline":{"business_name":lead.business.business_name,"niche":profile.niche if profile else "","audit_evidence":json.loads(audit.evidence) if audit else {"score_reasons":json.loads(lead.score_reasons)},"lead_score":{"score":lead.score,"grade":lead.grade,"reasons":json.loads(lead.score_reasons)},"service_profile":{"company_name":service.company_name,"description":service.description,"cta":service.cta} if service else {},"instruction_profile":{"id":profile.id,"name":profile.name,"offer":profile.offer,"cta":profile.cta} if profile else None,"engine":"DETERMINISTIC_EVIDENCE_BOUND"}}
