import base64, json, uuid
from datetime import datetime, timezone
import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, get_db
from app.models import AdminSetting, AuditLog, Business, BusinessSocialProfile, Call, Campaign, CampaignItem, Customer, InstructionProfile, Integration, Job, Lead, Message, Note, Payment, Project, ServiceProfile, TimelineEvent, VoiceAgentConfig, WebsiteAudit
from app.services.audit import audit_website
from app.services.intelligence import IntelligenceEngine
from app.services.jobs import LocalJobEngine
from app.services.google_places import GooglePlacesError, GooglePlacesProvider, normalize_place
from app.services.message_composer import MessageComposerEngine
from app.services.security import secret_store
from app.services.voice import LocalVoiceAgentProvider

app = FastAPI(title="LeadPilot API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_methods=["*"], allow_headers=["*"])
jobs = LocalJobEngine()

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
class StatusIn(BaseModel): status: str = Field(min_length=1, max_length=30)
class CustomerIn(BaseModel): notes: str = ""
class ProjectIn(BaseModel): name:str=Field(min_length=1,max_length=200); description:str=""; status:str="PLANNED"; start_date:str|None=None; due_date:str|None=None; amount:int=Field(default=0,ge=0); notes:str=""
class NoteIn(BaseModel): content:str=Field(min_length=1)
class PaymentIn(BaseModel): amount:int=Field(ge=0); currency:str="USD"; provider:str=""; status:str="PENDING"; reference:str=""
class CampaignIn(BaseModel): name:str=Field(min_length=1,max_length=200); channel:str="EMAIL"; sender_account:str=Field(default="",max_length=320); instruction_profile_id:int|None=None; lead_ids:list[int]=[]
class IntegrationConfigIn(BaseModel): account_name:str=""; secret_value:str=""; enabled:bool=True
class AdminSettingIn(BaseModel): key: str = Field(min_length=1, max_length=120); value: str = ""; protected: bool = False
class EmailSendIn(BaseModel): recipient:str=Field(min_length=3,max_length=320); subject:str=Field(min_length=1,max_length=300); content:str=Field(min_length=1)
class SocialProfileIn(BaseModel): platform:str=Field(min_length=2,max_length=30); profile_url:str=Field(min_length=8,max_length=2000); username:str|None=None; source:str="USER_STORED"

@app.middleware("http")
async def request_id(request:Request, call_next):
    request_id=str(uuid.uuid4())
    try:
        response=await call_next(request); result="SUCCESS" if response.status_code<400 else "ERROR"; safe_error=""
    except Exception:
        result="ERROR";safe_error="Unhandled request error";raise
    finally:
        db=SessionLocal();db.add(AuditLog(action=f"{request.method} {request.url.path}",subsystem="API",result=locals().get("result","ERROR"),request_id=request_id,safe_error=locals().get("safe_error","")));db.commit();db.close()
    response.headers["X-Request-ID"]=request_id; return response
@app.get("/api/v1/health")
def health(): return {"status":"WORKING","database":"SQLITE","jobs":"LOCAL_PERSISTENT","dry_run":settings.dry_run,"ai":"DETERMINISTIC_LOCAL"}
@app.post("/api/v1/audits")
async def audit(payload:dict):
    if not isinstance(payload.get("url"),str): raise HTTPException(422,detail="url is required")
    try:return await audit_website(payload["url"])
    except ValueError as exc:raise HTTPException(422,detail=str(exc)) from exc
    except Exception as exc:raise HTTPException(502,detail="WEBSITE_UNREACHABLE") from exc
@app.get("/api/v1/admin/instructions")
def list_instructions(db:Session=Depends(get_db)): return db.query(InstructionProfile).order_by(InstructionProfile.id.desc()).all()
@app.post("/api/v1/admin/instructions",status_code=201)
def create_instruction(data:InstructionIn,db:Session=Depends(get_db)):
    if db.query(InstructionProfile).filter_by(name=data.name).first():raise HTTPException(409,detail="Profile name already exists")
    item=InstructionProfile(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item
@app.put("/api/v1/admin/instructions/{profile_id}")
def update_instruction(profile_id:int,data:InstructionIn,db:Session=Depends(get_db)):
    item=db.get(InstructionProfile,profile_id)
    if not item:raise HTTPException(404,detail="Instruction profile not found")
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.commit();db.refresh(item);return item
@app.delete("/api/v1/admin/instructions/{profile_id}",status_code=204)
def delete_instruction(profile_id:int,db:Session=Depends(get_db)):
    item=db.get(InstructionProfile,profile_id)
    if not item:raise HTTPException(404,detail="Instruction profile not found")
    db.delete(item);db.commit()
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
def get_voice(db:Session=Depends(get_db)):
    config=db.query(VoiceAgentConfig).first()
    if not config:
        return {"status":"NOT_CONFIGURED","name":"Local voice agent","base_url":"","health_path":"/health","call_path":"/calls","enabled":False}
    return {"id": config.id, "name": config.name, "base_url": config.base_url, "health_path": config.health_path, "call_path": config.call_path, "enabled": config.enabled, "status": LocalVoiceAgentProvider(config).status}
@app.put("/api/v1/admin/voice-agent")
def save_voice(data:VoiceIn,db:Session=Depends(get_db)):
    config=db.query(VoiceAgentConfig).first() or VoiceAgentConfig()
    for key,value in data.model_dump().items():setattr(config,key,value)
    db.add(config);db.commit();db.refresh(config);return get_voice(db)
@app.post("/api/v1/admin/voice-agent/test")
async def test_voice(db:Session=Depends(get_db)):
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
def list_logs(db:Session=Depends(get_db)):return db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()

def safe_integration(item:Integration, provider:str):
    return {"provider":provider,"status":item.status or "NOT_CONFIGURED","account_name":item.account_name or "","capabilities":json.loads(item.capabilities or "[]"),"enabled":bool(item.enabled),"last_error":item.last_error or "","last_verified":item.last_test_at,"configured":bool(item.secret_value)}


def google_provider(db:Session) -> GooglePlacesProvider:
    item=db.query(Integration).filter_by(provider="GOOGLE_PLACES").first()
    secret = secret_store.decrypt(item.secret_value) if item and item.secret_value else ""
    return GooglePlacesProvider(secret) if secret else GooglePlacesProvider()


@app.get("/api/v1/admin/settings")
def list_admin_settings(db:Session=Depends(get_db)):
    settings_items = db.query(AdminSetting).order_by(AdminSetting.key.asc()).all()
    payload = []
    for item in settings_items:
        value = item.value if not item.protected else secret_store.mask(item.value)
        payload.append({"key": item.key, "value": value, "protected": item.protected})
    return payload


@app.put("/api/v1/admin/settings/{key}")
def upsert_admin_setting(key: str, data: AdminSettingIn, db: Session = Depends(get_db)):
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
def list_integrations(db:Session=Depends(get_db)):
    providers=["GOOGLE_PLACES","GMAIL","WHATSAPP","INSTAGRAM","FACEBOOK","LINKEDIN","X","TIKTOK","VOICE_AGENT","PAYMENTS"]
    return [safe_integration(db.query(Integration).filter_by(provider=provider).first() or Integration(provider=provider),provider) for provider in providers]

@app.get("/api/v1/admin/integrations/{provider}")
def get_integration(provider:str,db:Session=Depends(get_db)):
    name=provider.upper().replace("-","_"); item=db.query(Integration).filter_by(provider=name).first() or Integration(provider=name)
    return safe_integration(item,name)

@app.put("/api/v1/admin/integrations/{provider}")
def configure_integration(provider:str,data:IntegrationConfigIn,db:Session=Depends(get_db)):
    name=provider.upper().replace("-","_"); item=db.query(Integration).filter_by(provider=name).first() or Integration(provider=name)
    item.account_name=data.account_name; item.enabled=data.enabled
    if data.secret_value:
        item.secret_value = secret_store.encrypt(data.secret_value)
    item.status="CONFIGURED" if item.enabled and (data.secret_value or item.secret_value) else "NOT_CONFIGURED"; item.last_error=""
    db.add(item); db.commit(); db.refresh(item); return safe_integration(item,name)

@app.delete("/api/v1/admin/integrations/{provider}",status_code=204)
def disconnect_integration(provider:str,db:Session=Depends(get_db)):
    item=db.query(Integration).filter_by(provider=provider.upper()).first()
    if item: item.secret_value=""; item.account_name=""; item.enabled=False; item.status="NOT_CONFIGURED"; item.last_error=""; db.commit()

@app.post("/api/v1/admin/integrations/gmail/test")
async def test_gmail(db:Session=Depends(get_db)):
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
async def test_social_provider(provider:str,db:Session=Depends(get_db)):
    name=provider.upper().replace("-","_")
    if name in {"GOOGLE_PLACES","GMAIL"}: raise HTTPException(404,detail="Use the provider-specific test route")
    item=db.query(Integration).filter_by(provider=name).first()
    if not item or not item.secret_value: raise HTTPException(503,detail=f"{name}_NOT_CONFIGURED")
    item.status="CAPABILITY_UNAVAILABLE"; item.last_error="Official provider verification requires OAuth onboarding and approved capabilities"; item.last_test_at=datetime.now(timezone.utc); db.commit()
    raise HTTPException(503,detail="CAPABILITY_UNAVAILABLE")
@app.get("/api/v1/admin/integrations/google-places")
def google_status(db:Session=Depends(get_db)):
    item=db.query(Integration).filter_by(provider="GOOGLE_PLACES").first()
    if item and item.secret_value: return safe_integration(item,"GOOGLE_PLACES")
    return {"provider":"GOOGLE_PLACES","status":"CONFIGURED" if GooglePlacesProvider().configured() else "NOT_CONFIGURED","account_name":"","capabilities":[],"enabled":False,"last_error":"","last_verified":None,"configured":GooglePlacesProvider().configured()}

@app.put("/api/v1/admin/integrations/google-places")
def configure_google(data:IntegrationConfigIn,db:Session=Depends(get_db)): return configure_integration("GOOGLE_PLACES",data,db)

@app.delete("/api/v1/admin/integrations/google-places",status_code=204)
def remove_google(db:Session=Depends(get_db)): return disconnect_integration("GOOGLE_PLACES",db)
@app.post("/api/v1/admin/integrations/google-places/test")
async def test_google(db:Session=Depends(get_db)):
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

@app.post("/api/v1/campaigns",status_code=201)
def create_campaign(data:CampaignIn,db:Session=Depends(get_db)):
    if not data.sender_account: raise HTTPException(422,detail="Select a connected user sender account")
    campaign=Campaign(name=data.name,channel=data.channel,sender_account=data.sender_account,instruction_profile_id=data.instruction_profile_id); db.add(campaign); db.flush()
    for lead_id in data.lead_ids:
        if db.get(Lead,lead_id): db.add(CampaignItem(campaign_id=campaign.id,lead_id=lead_id))
    db.commit(); db.refresh(campaign); return campaign

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
def get_service_profile(db:Session=Depends(get_db)):return db.query(ServiceProfile).first() or {}
@app.put("/api/v1/admin/service-profile")
def save_service_profile(data:ServiceIn,db:Session=Depends(get_db)):
    item=db.query(ServiceProfile).first() or ServiceProfile()
    for key,value in data.model_dump().items():setattr(item,key,value)
    db.add(item);db.commit();db.refresh(item);return item
@app.get("/api/v1/admin/instructions/{profile_id}/test")
def test_instruction_profile(profile_id:int, db:Session=Depends(get_db)):
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
def activate_instruction_profile(profile_id:int, db:Session=Depends(get_db)):
    profile = db.get(InstructionProfile, profile_id)
    if not profile: raise HTTPException(404, detail="Instruction profile not found")
    for row in db.query(InstructionProfile).all():
        row.active = row.id == profile_id
    db.commit()
    profile.active = True
    db.commit()
    return {"id": profile.id, "active": True, "name": profile.name}


@app.post("/api/v1/admin/instructions/{profile_id}/duplicate")
def duplicate_instruction_profile(profile_id:int, db:Session=Depends(get_db)):
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
    draft = composer.compose(
        profile=profile,
        business_name=lead.business.business_name,
        offer=profile.offer if profile else service.offer if service else "",
        service_summary=service_summary,
        cta=profile.cta if profile else service.cta if service else "Book a quick strategy call",
        evidence=evidence,
        tone=profile.tone if profile else service.preferred_tone if service else "Professional",
        niche=profile.niche if profile else "",
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
@app.post("/api/v1/leads/{lead_id}/personalize",status_code=201)
def personalize(lead_id:int,data:DraftIn,db:Session=Depends(get_db)):
    """Explicit traceable pipeline: all returned context is persisted application data."""
    message=create_draft(lead_id,data,db); lead=db.get(Lead,lead_id); profile=db.get(InstructionProfile,message.instruction_profile_id) if message.instruction_profile_id else None
    audit=db.query(WebsiteAudit).filter_by(business_id=lead.business_id).first(); service=db.query(ServiceProfile).first()
    return {"message":message,"pipeline":{"business_name":lead.business.business_name,"niche":profile.niche if profile else "","audit_evidence":json.loads(audit.evidence) if audit else {"score_reasons":json.loads(lead.score_reasons)},"lead_score":{"score":lead.score,"grade":lead.grade,"reasons":json.loads(lead.score_reasons)},"service_profile":{"company_name":service.company_name,"description":service.description,"cta":service.cta} if service else {},"instruction_profile":{"id":profile.id,"name":profile.name,"offer":profile.offer,"cta":profile.cta} if profile else None,"engine":"DETERMINISTIC_EVIDENCE_BOUND"}}
