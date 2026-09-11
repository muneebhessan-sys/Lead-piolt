"""add persistent CRM workflow entities"""
from alembic import op
import sqlalchemy as sa

revision = "0006_crm_workflows"
down_revision = "0005_audit_logs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("customers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), unique=True), sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("notes", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_customers_lead_id", "customers", ["lead_id"])
    op.create_index("ix_customers_business_id", "customers", ["business_id"])
    op.create_table("projects", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("start_date", sa.String(20)), sa.Column("due_date", sa.String(20)), sa.Column("amount", sa.Integer(), nullable=False), sa.Column("notes", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"])
    op.create_table("calls", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id")), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id")), sa.Column("status", sa.String(40), nullable=False), sa.Column("provider_reference", sa.String(200), nullable=False), sa.Column("result", sa.Text(), nullable=False), sa.Column("error", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_calls_lead_id", "calls", ["lead_id"])
    op.create_index("ix_calls_customer_id", "calls", ["customer_id"])
    op.create_table("notes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id")), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id")), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_notes_lead_id", "notes", ["lead_id"])
    op.create_index("ix_notes_customer_id", "notes", ["customer_id"])
    op.create_table("timeline_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id")), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id")), sa.Column("event_type", sa.String(60), nullable=False), sa.Column("detail", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_timeline_events_lead_id", "timeline_events", ["lead_id"])
    op.create_index("ix_timeline_events_customer_id", "timeline_events", ["customer_id"])
    op.create_table("payments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False), sa.Column("amount", sa.Integer(), nullable=False), sa.Column("currency", sa.String(8), nullable=False), sa.Column("provider", sa.String(80), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("reference", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"])
    op.create_table("campaigns", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("channel", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("instruction_profile_id", sa.Integer(), sa.ForeignKey("instruction_profiles.id")), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_table("campaign_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False), sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=False), sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id")), sa.Column("status", sa.String(30), nullable=False))
    op.create_index("ix_campaign_items_campaign_id", "campaign_items", ["campaign_id"])
    op.create_index("ix_campaign_items_lead_id", "campaign_items", ["lead_id"])

def downgrade():
    for table in ("campaign_items", "campaigns", "payments", "timeline_events", "notes", "calls", "projects", "customers"):
        op.drop_table(table)