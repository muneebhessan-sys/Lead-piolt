"""add instruction_versions, message_templates, accounts, voice_agents, system_settings, oauth_states, campaign_messages, call_details, audit_log_details, extend campaigns, calls, audit_logs, integrations, voice_agent_configs"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011_extended_models"
down_revision = "0010_admin_settings"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing_tables = set(sa.inspect(bind).get_table_names())
    existing_columns = {
        table: {column["name"] for column in sa.inspect(bind).get_columns(table)}
        for table in existing_tables
    }
    existing_indexes = {
        table: {index["name"] for index in sa.inspect(bind).get_indexes(table)}
        for table in existing_tables
    }

    # instruction_versions
    if "instruction_versions" not in existing_tables:
        op.create_table(
            "instruction_versions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("instruction_profile_id", sa.Integer(), sa.ForeignKey("instruction_profiles.id"), index=True, nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("niche", sa.String(160), nullable=False, server_default=""),
            sa.Column("language", sa.String(40), nullable=False, server_default="English"),
            sa.Column("tone", sa.String(80), nullable=False, server_default="Professional"),
            sa.Column("offer", sa.Text(), nullable=False, server_default=""),
            sa.Column("services", sa.Text(), nullable=False, server_default=""),
            sa.Column("cta", sa.Text(), nullable=False, server_default=""),
            sa.Column("rules", sa.Text(), nullable=False, server_default=""),
            sa.Column("do_not_say", sa.Text(), nullable=False, server_default=""),
            sa.Column("personalization_rules", sa.Text(), nullable=False, server_default=""),
            sa.Column("additional_instructions", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "ix_instruction_versions_status" not in existing_indexes.get("instruction_versions", set()):
        op.create_index("ix_instruction_versions_status", "instruction_versions", ["status"])

    # message_templates
    if "message_templates" not in existing_tables:
        op.create_table(
            "message_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("template_type", sa.String(20), nullable=False, server_default="EMAIL"),
        sa.Column("subject", sa.String(300), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("variables", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    if "ix_message_templates_name" not in existing_indexes.get("message_templates", set()):
        op.create_index("ix_message_templates_type", "message_templates", ["template_type"])

    # accounts
    if "accounts" not in existing_tables:
        op.create_table(
            "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING_VERIFICATION"),
        sa.Column("provider", sa.String(80), nullable=False, server_default=""),
        sa.Column("provider_user_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settings", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # voice_agents
    if "voice_agents" not in existing_tables:
        op.create_table(
            "voice_agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False, server_default="local"),
        sa.Column("base_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False, server_default=""),
        sa.Column("config", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="INACTIVE"),
        sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # system_settings
    if "system_settings" not in existing_tables:
        op.create_table(
            "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(120), nullable=False, unique=True),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("value_type", sa.String(30), nullable=False, server_default="string"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("category", sa.String(80), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # oauth_states
    if "oauth_states" not in existing_tables:
        op.create_table(
            "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state", sa.String(128), nullable=False, unique=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("code_verifier", sa.String(128), nullable=False, server_default=""),
        sa.Column("scopes", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # campaign_messages
    if "campaign_messages" not in existing_tables:
        op.create_table(
            "campaign_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), index=True, nullable=False),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), index=True, nullable=False),
        sa.Column("message_template_id", sa.Integer(), sa.ForeignKey("message_templates.id"), nullable=True),
        sa.Column("instruction_version_id", sa.Integer(), sa.ForeignKey("instruction_versions.id"), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False, server_default="EMAIL"),
        sa.Column("recipient", sa.String(320), nullable=False, server_default=""),
        sa.Column("subject", sa.String(300), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("provider_message_id", sa.String(200), nullable=False, server_default=""),
        sa.Column("error", sa.Text(), nullable=False, server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # call_details
    if "call_details" not in existing_tables:
        op.create_table(
            "call_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("call_id", sa.Integer(), sa.ForeignKey("calls.id"), unique=True, index=True, nullable=False),
        sa.Column("voice_agent_id", sa.Integer(), sa.ForeignKey("voice_agents.id"), nullable=True),
        sa.Column("direction", sa.String(20), nullable=False, server_default="OUTBOUND"),
        sa.Column("from_number", sa.String(80), nullable=False, server_default=""),
        sa.Column("to_number", sa.String(80), nullable=False, server_default=""),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recording_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("transcript", sa.Text(), nullable=False, server_default=""),
        sa.Column("cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_data", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # audit_log_details
    if "audit_log_details" not in existing_tables:
        op.create_table(
            "audit_log_details",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("audit_log_id", sa.Integer(), sa.ForeignKey("audit_logs.id"), unique=True, index=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=False, server_default=""),
        sa.Column("user_agent", sa.Text(), nullable=False, server_default=""),
        sa.Column("resource_type", sa.String(80), nullable=False, server_default=""),
        sa.Column("resource_id", sa.String(80), nullable=False, server_default=""),
        sa.Column("old_values", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("new_values", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # Extend campaigns table
    op.add_column("campaigns", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("campaigns", sa.Column("sender_account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))
    op.add_column("campaigns", sa.Column("instruction_version_id", sa.Integer(), sa.ForeignKey("instruction_versions.id"), nullable=True))
    op.add_column("campaigns", sa.Column("message_template_id", sa.Integer(), sa.ForeignKey("message_templates.id"), nullable=True))
    op.add_column("campaigns", sa.Column("schedule_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("campaigns", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("campaigns", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("campaigns", sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("campaigns", sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("campaigns", sa.Column("delivered_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("campaigns", sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("campaigns", sa.Column("settings", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("campaigns", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_sender_account_id", "campaigns", ["sender_account_id"])

    # Extend calls table
    op.add_column("calls", sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=True))
    op.add_column("calls", sa.Column("voice_agent_id", sa.Integer(), sa.ForeignKey("voice_agents.id"), nullable=True))
    op.add_column("calls", sa.Column("direction", sa.String(20), nullable=False, server_default="OUTBOUND"))
    op.add_column("calls", sa.Column("from_number", sa.String(80), nullable=False, server_default=""))
    op.add_column("calls", sa.Column("to_number", sa.String(80), nullable=False, server_default=""))
    op.add_column("calls", sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("calls", sa.Column("recording_url", sa.Text(), nullable=False, server_default=""))
    op.add_column("calls", sa.Column("transcript", sa.Text(), nullable=False, server_default=""))
    op.add_column("calls", sa.Column("cost", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("calls", sa.Column("provider_data", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("calls", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calls", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_calls_campaign_id", "calls", ["campaign_id"])
    op.create_index("ix_calls_voice_agent_id", "calls", ["voice_agent_id"])

    # Extend audit_logs table
    op.add_column("audit_logs", sa.Column("user_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))
    op.add_column("audit_logs", sa.Column("ip_address", sa.String(45), nullable=False, server_default=""))
    op.add_column("audit_logs", sa.Column("user_agent", sa.Text(), nullable=False, server_default=""))
    op.add_column("audit_logs", sa.Column("resource_type", sa.String(80), nullable=False, server_default=""))
    op.add_column("audit_logs", sa.Column("resource_id", sa.String(80), nullable=False, server_default=""))
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    # Extend integrations table - change status to enum
    op.alter_column("integrations", "status", existing_type=sa.String(40), type_=sa.String(30), existing_nullable=False, existing_server_default=sa.text("'NOT_CONFIGURED'"))

    # Extend voice_agent_configs table
    op.add_column("voice_agent_configs", sa.Column("status", sa.String(20), nullable=False, server_default="INACTIVE"))
    op.add_column("voice_agent_configs", sa.Column("last_health_check", sa.DateTime(timezone=True), nullable=True))
    op.add_column("voice_agent_configs", sa.Column("last_error", sa.Text(), nullable=False, server_default=""))
    op.add_column("voice_agent_configs", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.add_column("voice_agent_configs", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.create_index("ix_voice_agent_configs_status", "voice_agent_configs", ["status"])


def downgrade():
    # Drop indexes first
    op.drop_index("ix_voice_agent_configs_status", table_name="voice_agent_configs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_calls_voice_agent_id", table_name="calls")
    op.drop_index("ix_calls_campaign_id", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_campaigns_sender_account_id", table_name="campaigns")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaign_messages_lead_id", table_name="campaign_messages")
    op.drop_index("ix_campaign_messages_campaign_id", table_name="campaign_messages")
    op.drop_index("ix_oauth_states_account_id", table_name="oauth_states")
    op.drop_index("ix_oauth_states_expires_at", table_name="oauth_states")
    op.drop_index("ix_oauth_states_provider", table_name="oauth_states")
    op.drop_index("ix_oauth_states_state", table_name="oauth_states")
    op.drop_index("ix_system_settings_category", table_name="system_settings")
    op.drop_index("ix_system_settings_key", table_name="system_settings")
    op.drop_index("ix_voice_agents_name", table_name="voice_agents")
    op.drop_index("ix_voice_agents_status", table_name="voice_agents")
    op.drop_index("ix_accounts_email", table_name="accounts")
    op.drop_index("ix_accounts_status", table_name="accounts")
    op.drop_index("ix_message_templates_name", table_name="message_templates")
    op.drop_index("ix_message_templates_type", table_name="message_templates")
    op.drop_index("ix_instruction_versions_status", table_name="instruction_versions")

    # Drop columns from existing tables
    op.drop_column("voice_agent_configs", "updated_at")
    op.drop_column("voice_agent_configs", "created_at")
    op.drop_column("voice_agent_configs", "last_error")
    op.drop_column("voice_agent_configs", "last_health_check")
    op.drop_column("voice_agent_configs", "status")
    op.alter_column("integrations", "status", existing_type=sa.String(30), type_=sa.String(40), existing_nullable=False, existing_server_default=sa.text("'NOT_CONFIGURED'"))
    op.drop_column("audit_logs", "resource_id")
    op.drop_column("audit_logs", "resource_type")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "ip_address")
    op.drop_column("audit_logs", "user_id")
    op.drop_column("calls", "updated_at")
    op.drop_column("calls", "ended_at")
    op.drop_column("calls", "started_at")
    op.drop_column("calls", "provider_data")
    op.drop_column("calls", "cost")
    op.drop_column("calls", "transcript")
    op.drop_column("calls", "recording_url")
    op.drop_column("calls", "duration_seconds")
    op.drop_column("calls", "to_number")
    op.drop_column("calls", "from_number")
    op.drop_column("calls", "direction")
    op.drop_column("calls", "voice_agent_id")
    op.drop_column("calls", "campaign_id")
    op.drop_column("campaigns", "updated_at")
    op.drop_column("campaigns", "settings")
    op.drop_column("campaigns", "failed_count")
    op.drop_column("campaigns", "delivered_count")
    op.drop_column("campaigns", "sent_count")
    op.drop_column("campaigns", "total_recipients")
    op.drop_column("campaigns", "completed_at")
    op.drop_column("campaigns", "started_at")
    op.drop_column("campaigns", "schedule_at")
    op.drop_column("campaigns", "message_template_id")
    op.drop_column("campaigns", "instruction_version_id")
    op.drop_column("campaigns", "sender_account_id")
    op.drop_column("campaigns", "description")

    # Drop new tables
    op.drop_table("audit_log_details")
    op.drop_table("call_details")
    op.drop_table("campaign_messages")
    op.drop_table("oauth_states")
    op.drop_table("system_settings")
    op.drop_table("voice_agents")
    op.drop_table("accounts")
    op.drop_table("message_templates")
    op.drop_table("instruction_versions")