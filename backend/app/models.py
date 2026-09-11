from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

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
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)

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

class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="NOT_CONFIGURED")
    account_name: Mapped[str] = mapped_column(String(200), default="")
    capabilities: Mapped[str] = mapped_column(Text, default="[]")
    secret_value: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_error: Mapped[str] = mapped_column(Text, default="")
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    subsystem: Mapped[str] = mapped_column(String(80), index=True)
    result: Mapped[str] = mapped_column(String(40))
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    safe_error: Mapped[str] = mapped_column(Text, default="")
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
    status: Mapped[str] = mapped_column(String(40), default="QUEUED")
    provider_reference: Mapped[str] = mapped_column(String(200), default="")
    result: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

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
    channel: Mapped[str] = mapped_column(String(30), default="EMAIL")
    sender_account: Mapped[str] = mapped_column(String(320), default="")
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    instruction_profile_id: Mapped[int | None] = mapped_column(ForeignKey("instruction_profiles.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class CampaignItem(Base):
    __tablename__ = "campaign_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
