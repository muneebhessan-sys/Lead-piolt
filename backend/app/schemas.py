from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field



class InstructionVersionStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MessageTemplateType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    VOICE = "VOICE"
    WHATSAPP = "WHATSAPP"


class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class IntegrationStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class VoiceAgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CampaignMessageStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class CallStatus(str, Enum):
    QUEUED = "QUEUED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"


class AuditActionType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class OAuthProvider(str, Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    LINKEDIN = "LINKEDIN"
    FACEBOOK = "FACEBOOK"
    TWITTER = "TWITTER"
    GITHUB = "GITHUB"


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class InstructionVersionBase(BaseSchema):
    instruction_profile_id: int
    version: int = 1
    status: InstructionVersionStatus = InstructionVersionStatus.DRAFT
    name: str = Field(max_length=160)
    niche: str = Field(default="", max_length=160)
    language: str = Field(default="English", max_length=40)
    tone: str = Field(default="Professional", max_length=80)
    offer: str = ""
    services: str = ""
    cta: str = ""
    rules: str = ""
    do_not_say: str = ""
    personalization_rules: str = ""
    additional_instructions: str = ""


class InstructionVersionCreate(InstructionVersionBase):
    pass


class InstructionVersionUpdate(BaseSchema):
    status: Optional[InstructionVersionStatus] = None
    name: Optional[str] = Field(default=None, max_length=160)
    niche: Optional[str] = Field(default=None, max_length=160)
    language: Optional[str] = Field(default=None, max_length=40)
    tone: Optional[str] = Field(default=None, max_length=80)
    offer: Optional[str] = None
    services: Optional[str] = None
    cta: Optional[str] = None
    rules: Optional[str] = None
    do_not_say: Optional[str] = None
    personalization_rules: Optional[str] = None
    additional_instructions: Optional[str] = None


class InstructionVersionResponse(InstructionVersionBase):
    id: int
    created_at: datetime
    activated_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class MessageTemplateBase(BaseSchema):
    name: str = Field(max_length=200)
    template_type: MessageTemplateType = MessageTemplateType.EMAIL
    subject: str = Field(default="", max_length=300)
    content: str
    variables: str = "[]"
    description: str = ""
    is_system: bool = False


class MessageTemplateCreate(MessageTemplateBase):
    pass


class MessageTemplateUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, max_length=200)
    template_type: Optional[MessageTemplateType] = None
    subject: Optional[str] = Field(default=None, max_length=300)
    content: Optional[str] = None
    variables: Optional[str] = None
    description: Optional[str] = None
    is_system: Optional[bool] = None


class MessageTemplateResponse(MessageTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AccountBase(BaseSchema):
    email: str = Field(max_length=320)
    name: str = Field(max_length=200)
    status: AccountStatus = AccountStatus.PENDING_VERIFICATION
    provider: str = Field(default="", max_length=80)
    provider_user_id: str = Field(default="", max_length=200)
    settings: str = "{}"


class AccountCreate(AccountBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class AccountUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, max_length=200)
    status: Optional[AccountStatus] = None
    provider: Optional[str] = Field(default=None, max_length=80)
    provider_user_id: Optional[str] = Field(default=None, max_length=200)
    settings: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class AccountResponse(AccountBase):
    id: int
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class VoiceAgentBase(BaseSchema):
    name: str = Field(max_length=160)
    provider: str = Field(default="local", max_length=80)
    base_url: str = ""
    config: str = "{}"
    status: VoiceAgentStatus = VoiceAgentStatus.INACTIVE
    enabled: bool = False


class VoiceAgentCreate(VoiceAgentBase):
    api_key: Optional[str] = None


class VoiceAgentUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, max_length=160)
    provider: Optional[str] = Field(default=None, max_length=80)
    base_url: Optional[str] = None
    config: Optional[str] = None
    status: Optional[VoiceAgentStatus] = None
    enabled: Optional[bool] = None
    api_key: Optional[str] = None


class VoiceAgentResponse(VoiceAgentBase):
    id: int
    last_health_check: Optional[datetime] = None
    last_error: str = ""
    created_at: datetime
    updated_at: datetime


class SystemSettingBase(BaseSchema):
    key: str = Field(max_length=120)
    value: str = ""
    value_type: str = Field(default="string", max_length=30)
    description: str = ""
    is_secret: bool = False
    category: str = Field(default="general", max_length=80)


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseSchema):
    value: Optional[str] = None
    value_type: Optional[str] = Field(default=None, max_length=30)
    description: Optional[str] = None
    is_secret: Optional[bool] = None
    category: Optional[str] = Field(default=None, max_length=80)


class SystemSettingResponse(SystemSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime


class OAuthStateBase(BaseSchema):
    state: str = Field(max_length=128)
    provider: OAuthProvider
    redirect_uri: str
    code_verifier: str = Field(default="", max_length=128)
    scopes: str = "[]"
    account_id: Optional[int] = None
    expires_at: datetime


class OAuthStateCreate(OAuthStateBase):
    pass


class OAuthStateResponse(OAuthStateBase):
    id: int
    created_at: datetime
    used_at: Optional[datetime] = None


class CampaignBase(BaseSchema):
    name: str = Field(max_length=200)
    description: str = ""
    channel: str = Field(default="EMAIL", max_length=30)
    sender_account_id: Optional[int] = None
    sender_account: str = Field(default="", max_length=320)
    status: CampaignStatus = CampaignStatus.DRAFT
    instruction_profile_id: Optional[int] = None
    instruction_version_id: Optional[int] = None
    message_template_id: Optional[int] = None
    schedule_at: Optional[datetime] = None
    settings: str = "{}"


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    channel: Optional[str] = Field(default=None, max_length=30)
    sender_account_id: Optional[int] = None
    sender_account: Optional[str] = Field(default=None, max_length=320)
    status: Optional[CampaignStatus] = None
    instruction_profile_id: Optional[int] = None
    instruction_version_id: Optional[int] = None
    message_template_id: Optional[int] = None
    schedule_at: Optional[datetime] = None
    settings: Optional[str] = None


class CampaignResponse(CampaignBase):
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    created_at: datetime
    updated_at: datetime


class CampaignMessageBase(BaseSchema):
    campaign_id: int
    lead_id: int
    message_template_id: Optional[int] = None
    instruction_version_id: Optional[int] = None
    channel: str = Field(default="EMAIL", max_length=30)
    recipient: str = Field(default="", max_length=320)
    subject: str = Field(default="", max_length=300)
    content: str
    status: CampaignMessageStatus = CampaignMessageStatus.PENDING
    provider_message_id: str = Field(default="", max_length=200)
    error: str = ""


class CampaignMessageCreate(CampaignMessageBase):
    pass


class CampaignMessageUpdate(BaseSchema):
    status: Optional[CampaignMessageStatus] = None
    provider_message_id: Optional[str] = Field(default=None, max_length=200)
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class CampaignMessageResponse(CampaignMessageBase):
    id: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CallBase(BaseSchema):
    lead_id: Optional[int] = None
    customer_id: Optional[int] = None
    campaign_id: Optional[int] = None
    voice_agent_id: Optional[int] = None
    status: CallStatus = CallStatus.QUEUED
    provider_reference: str = Field(default="", max_length=200)
    direction: str = Field(default="OUTBOUND", max_length=20)
    from_number: str = Field(default="", max_length=80)
    to_number: str = Field(default="", max_length=80)


class CallCreate(CallBase):
    pass


class CallUpdate(BaseSchema):
    status: Optional[CallStatus] = None
    provider_reference: Optional[str] = Field(default=None, max_length=200)
    result: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    cost: Optional[int] = None
    provider_data: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class CallResponse(CallBase):
    id: int
    result: str = ""
    error: str = ""
    duration_seconds: int = 0
    recording_url: str = ""
    transcript: str = ""
    cost: int = 0
    provider_data: str = "{}"
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CallDetailBase(BaseSchema):
    call_id: int
    voice_agent_id: Optional[int] = None
    direction: str = Field(default="OUTBOUND", max_length=20)
    from_number: str = Field(default="", max_length=80)
    to_number: str = Field(default="", max_length=80)
    duration_seconds: int = 0
    recording_url: str = ""
    transcript: str = ""
    cost: int = 0
    provider_data: str = "{}"


class CallDetailCreate(CallDetailBase):
    pass


class CallDetailResponse(CallDetailBase):
    id: int
    created_at: datetime
    updated_at: datetime


class AuditLogBase(BaseSchema):
    action: AuditActionType
    subsystem: str = Field(max_length=80)
    result: str = Field(max_length=40)
    request_id: str = Field(max_length=64)
    safe_error: str = ""
    user_id: Optional[int] = None
    ip_address: str = Field(default="", max_length=45)
    user_agent: str = ""
    resource_type: str = Field(default="", max_length=80)
    resource_id: str = Field(default="", max_length=80)


class AuditLogCreate(AuditLogBase):
    pass


class AuditLogResponse(AuditLogBase):
    id: int
    created_at: datetime


class AuditLogDetailBase(BaseSchema):
    audit_log_id: int
    user_id: Optional[int] = None
    ip_address: str = Field(default="", max_length=45)
    user_agent: str = ""
    resource_type: str = Field(default="", max_length=80)
    resource_id: str = Field(default="", max_length=80)
    old_values: str = "{}"
    new_values: str = "{}"


class AuditLogDetailResponse(AuditLogDetailBase):
    id: int
    created_at: datetime


class IntegrationBase(BaseSchema):
    provider: str = Field(max_length=80)
    status: IntegrationStatus = IntegrationStatus.NOT_CONFIGURED
    account_name: str = Field(default="", max_length=200)
    capabilities: str = "[]"
    secret_value: str = ""
    enabled: bool = False
    last_error: str = ""


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseSchema):
    status: Optional[IntegrationStatus] = None
    account_name: Optional[str] = Field(default=None, max_length=200)
    capabilities: Optional[str] = None
    secret_value: Optional[str] = None
    enabled: Optional[bool] = None
    last_error: Optional[str] = None
    last_test_at: Optional[datetime] = None


class IntegrationResponse(IntegrationBase):
    id: int
    last_test_at: Optional[datetime] = None
    created_at: datetime


class VoiceAgentConfigBase(BaseSchema):
    name: str = Field(default="Local voice agent", max_length=160)
    base_url: str = ""
    health_path: str = Field(default="/health", max_length=200)
    call_path: str = Field(default="/calls", max_length=200)
    status: VoiceAgentStatus = VoiceAgentStatus.INACTIVE
    enabled: bool = False


class VoiceAgentConfigCreate(VoiceAgentConfigBase):
    pass


class VoiceAgentConfigUpdate(BaseSchema):
    name: Optional[str] = Field(default=None, max_length=160)
    base_url: Optional[str] = None
    health_path: Optional[str] = Field(default=None, max_length=200)
    call_path: Optional[str] = Field(default=None, max_length=200)
    status: Optional[VoiceAgentStatus] = None
    enabled: Optional[bool] = None
    last_health_check: Optional[datetime] = None
    last_error: Optional[str] = None


class VoiceAgentConfigResponse(VoiceAgentConfigBase):
    id: int
    last_health_check: Optional[datetime] = None
    last_error: str = ""
    created_at: datetime
    updated_at: datetime


T = TypeVar('T')


class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseSchema):
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseSchema):
    success: bool = True
    message: str = ""


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthCheckResponse(BaseSchema):
    status: str
    version: str
    database: str
    timestamp: datetime