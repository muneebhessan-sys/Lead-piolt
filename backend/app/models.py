from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass


class InstructionVersionStatus(str, PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MessageTemplateType(str, PyEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    VOICE = "VOICE"
    WHATSAPP = "WHATSAPP"


class AccountStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class IntegrationStatus(str, PyEnum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"
    DISCONNECTED = "DISCONNECTED"


class VoiceAgentStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"


class CampaignStatus(str, PyEnum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CampaignMessageStatus(str, PyEnum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class OutboundMessageStatus(str, PyEnum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    BOUNCED = "BOUNCED"


class CallStatus(str, PyEnum):
    QUEUED = "QUEUED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"


class AuditActionType(str, PyEnum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class OAuthProvider(str, PyEnum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    LINKEDIN = "LINKEDIN"
    FACEBOOK = "FACEBOOK"
    TWITTER = "TWITTER"
    GITHUB = "GITHUB"

class SearchJob(Base):
    __tablename__ = "search_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    niche: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="QUEUED")
    target_count: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class AdminSetting(Base):
    __tablename__ = "admin_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    protected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Business(Base):
    __tablename__ = "businesses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    business_name: Mapped[str] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    locality: Mapped[str | None] = mapped_column(String(160), nullable=True)
    city: Mapped[str | None] = mapped_column(String(160), nullable=True)
    region: Mapped[str | None] = mapped_column(String(160), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    categories: Mapped[str] = mapped_column(Text, default="[]")
    latitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rating: Mapped[str | None] = mapped_column(String(20), nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_status: Mapped[str] = mapped_column(String(30), default="CONTACTABLE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class BusinessSocialProfile(Base):
    __tablename__ = "business_social_profiles"
    __table_args__ = (UniqueConstraint("business_id", "platform", "profile_url", name="uq_business_social_profile"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    platform: Mapped[str] = mapped_column(String(30), index=True)
    profile_url: Mapped[str] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="USER_STORED")
    status: Mapped[str] = mapped_column(String(30), default="STORED")

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class InstructionProfile(Base):
    __tablename__ = "instruction_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    niche: Mapped[str] = mapped_column(String(160), default="")
    language: Mapped[str] = mapped_column(String(40), default="English")
    tone: Mapped[str] = mapped_column(String(80), default="Professional")
    offer: Mapped[str] = mapped_column(Text, default="")
    services: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(Text, default="")
    rules: Mapped[str] = mapped_column(Text, default="")
    do_not_say: Mapped[str] = mapped_column(Text, default="")
    personalization_rules: Mapped[str] = mapped_column(Text, default="")
    additional_instructions: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class VoiceAgentConfig(Base):
    __tablename__ = "voice_agent_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), default="Local voice agent")
    base_url: Mapped[str] = mapped_column(Text, default="")
    health_path: Mapped[str] = mapped_column(String(200), default="/health")
    call_path: Mapped[str] = mapped_column(String(200), default="/calls")
    status: Mapped[VoiceAgentStatus] = mapped_column(Enum(VoiceAgentStatus), default=VoiceAgentStatus.INACTIVE, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), unique=True, index=True)
    lifecycle: Mapped[str] = mapped_column(String(30), default="PROSPECT", index=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    grade: Mapped[str] = mapped_column(String(20), default="STANDARD")
    score_reasons: Mapped[str] = mapped_column(Text, default="[]")
    business: Mapped[Business] = relationship()

class WebsiteAudit(Base):
    __tablename__ = "website_audits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="UNVERIFIED")
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class ServiceProfile(Base):
    __tablename__ = "service_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    services: Mapped[str] = mapped_column(Text, default="")
    target_niches: Mapped[str] = mapped_column(Text, default="")
    target_locations: Mapped[str] = mapped_column(Text, default="")
    offer: Mapped[str] = mapped_column(Text, default="")
    portfolio_url: Mapped[str] = mapped_column(Text, default="")
    contact_information: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(Text, default="")
    preferred_tone: Mapped[str] = mapped_column(String(80), default="Professional")
    additional_instructions: Mapped[str] = mapped_column(Text, default="")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    instruction_profile_id: Mapped[int | None] = mapped_column(ForeignKey("instruction_profiles.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(30), default="EMAIL")
    recipient: Mapped[str] = mapped_column(String(320), default="")
    subject: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OutboundMessage(Base):
    __tablename__ = "outbound_messages"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_outbound_messages_idempotency_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True, index=True)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    recipient: Mapped[str] = mapped_column(String(320), default="")
    subject: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[OutboundMessageStatus] = mapped_column(Enum(OutboundMessageStatus), default=OutboundMessageStatus.PENDING, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_message_id: Mapped[str] = mapped_column(String(255), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_buckets"
    __table_args__ = (UniqueConstraint("provider", "window_start", name="uq_rate_limit_provider_window"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), unique=True)
    # Keep this as text because older local databases contain CONFIGURED.
    status: Mapped[str] = mapped_column(String(40), default=IntegrationStatus.NOT_CONFIGURED.value, index=True)
    account_name: Mapped[str] = mapped_column(String(200), default="")
    capabilities: Mapped[str] = mapped_column(Text, default="[]")
    secret_value: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[str] = mapped_column(Text, default="")
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[AuditActionType] = mapped_column(Enum(AuditActionType), index=True)
    subsystem: Mapped[str] = mapped_column(String(80), index=True)
    result: Mapped[str] = mapped_column(String(40))
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    safe_error: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    resource_type: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), unique=True, nullable=True, index=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="PLANNED")
    start_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Call(Base):
    __tablename__ = "calls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey("campaigns.id"), nullable=True, index=True)
    voice_agent_id: Mapped[int | None] = mapped_column(ForeignKey("voice_agents.id"), nullable=True, index=True)
    status: Mapped[CallStatus] = mapped_column(Enum(CallStatus), default=CallStatus.QUEUED, index=True)
    provider_reference: Mapped[str] = mapped_column(String(200), default="")
    direction: Mapped[str] = mapped_column(String(20), default="OUTBOUND")
    from_number: Mapped[str] = mapped_column(String(80), default="")
    to_number: Mapped[str] = mapped_column(String(80), default="")
    result: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    recording_url: Mapped[str] = mapped_column(Text, default="")
    transcript: Mapped[str] = mapped_column(Text, default="")
    cost: Mapped[int] = mapped_column(Integer, default=0)
    provider_data: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    provider: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    reference: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    channel: Mapped[str] = mapped_column(String(30), default="EMAIL")
    sender_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    sender_account: Mapped[str] = mapped_column(String(320), default="")
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, index=True)
    instruction_profile_id: Mapped[int | None] = mapped_column(ForeignKey("instruction_profiles.id"), nullable=True)
    instruction_version_id: Mapped[int | None] = mapped_column(ForeignKey("instruction_versions.id"), nullable=True)
    message_template_id: Mapped[int | None] = mapped_column(ForeignKey("message_templates.id"), nullable=True)
    schedule_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    settings: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class CampaignItem(Base):
    __tablename__ = "campaign_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")


class InstructionVersion(Base):
    __tablename__ = "instruction_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instruction_profile_id: Mapped[int] = mapped_column(ForeignKey("instruction_profiles.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[InstructionVersionStatus] = mapped_column(Enum(InstructionVersionStatus), default=InstructionVersionStatus.DRAFT, index=True)
    name: Mapped[str] = mapped_column(String(160))
    niche: Mapped[str] = mapped_column(String(160), default="")
    language: Mapped[str] = mapped_column(String(40), default="English")
    tone: Mapped[str] = mapped_column(String(80), default="Professional")
    offer: Mapped[str] = mapped_column(Text, default="")
    services: Mapped[str] = mapped_column(Text, default="")
    cta: Mapped[str] = mapped_column(Text, default="")
    rules: Mapped[str] = mapped_column(Text, default="")
    do_not_say: Mapped[str] = mapped_column(Text, default="")
    personalization_rules: Mapped[str] = mapped_column(Text, default="")
    additional_instructions: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("instruction_profile_id", "version", name="uq_instruction_version"),)


class MessageTemplate(Base):
    __tablename__ = "message_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    template_type: Mapped[MessageTemplateType] = mapped_column(Enum(MessageTemplateType), default=MessageTemplateType.EMAIL, index=True)
    subject: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text)
    variables: Mapped[str] = mapped_column(Text, default="[]")
    description: Mapped[str] = mapped_column(Text, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[AccountStatus] = mapped_column(Enum(AccountStatus), default=AccountStatus.PENDING_VERIFICATION, index=True)
    provider: Mapped[str] = mapped_column(String(80), default="")
    provider_user_id: Mapped[str] = mapped_column(String(200), default="")
    access_token_encrypted: Mapped[str] = mapped_column(Text, default="")
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, default="")
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settings: Mapped[str] = mapped_column(Text, default="{}")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VoiceAgent(Base):
    __tablename__ = "voice_agents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    provider: Mapped[str] = mapped_column(String(80), default="local")
    base_url: Mapped[str] = mapped_column(Text, default="")
    api_key_encrypted: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[VoiceAgentStatus] = mapped_column(Enum(VoiceAgentStatus), default=VoiceAgentStatus.INACTIVE, index=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    value_type: Mapped[str] = mapped_column(String(30), default="string")
    description: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str] = mapped_column(String(80), default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OAuthState(Base):
    __tablename__ = "oauth_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    provider: Mapped[OAuthProvider] = mapped_column(Enum(OAuthProvider), index=True)
    redirect_uri: Mapped[str] = mapped_column(Text)
    code_verifier: Mapped[str] = mapped_column(String(128), default="")
    scopes: Mapped[str] = mapped_column(Text, default="[]")
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CampaignMessage(Base):
    __tablename__ = "campaign_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    message_template_id: Mapped[int | None] = mapped_column(ForeignKey("message_templates.id"), nullable=True)
    instruction_version_id: Mapped[int | None] = mapped_column(ForeignKey("instruction_versions.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(30), default="EMAIL")
    recipient: Mapped[str] = mapped_column(String(320), default="")
    subject: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[CampaignMessageStatus] = mapped_column(Enum(CampaignMessageStatus), default=CampaignMessageStatus.PENDING, index=True)
    provider_message_id: Mapped[str] = mapped_column(String(200), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CallExtended(Base):
    __tablename__ = "call_details"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), unique=True, index=True)
    voice_agent_id: Mapped[int | None] = mapped_column(ForeignKey("voice_agents.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20), default="OUTBOUND")
    from_number: Mapped[str] = mapped_column(String(80), default="")
    to_number: Mapped[str] = mapped_column(String(80), default="")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    recording_url: Mapped[str] = mapped_column(Text, default="")
    transcript: Mapped[str] = mapped_column(Text, default="")
    cost: Mapped[int] = mapped_column(Integer, default=0)
    provider_data: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLogExtended(Base):
    __tablename__ = "audit_log_details"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_log_id: Mapped[int] = mapped_column(ForeignKey("audit_logs.id"), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    resource_type: Mapped[str] = mapped_column(String(80), default="")
    resource_id: Mapped[str] = mapped_column(String(80), default="")
    old_values: Mapped[str] = mapped_column(Text, default="{}")
    new_values: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
