"""Add outbound message idempotency and persistent rate-limit buckets."""

from alembic import op
import sqlalchemy as sa


revision = "0013_outbound_messaging"
down_revision = "0012_theme_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "outbound_messages" not in tables:
        op.create_table(
            "outbound_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id"), nullable=True),
            sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=True),
            sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
            sa.Column("channel", sa.String(30), nullable=False),
            sa.Column("recipient", sa.String(320), nullable=False, server_default=""),
            sa.Column("subject", sa.String(300), nullable=False, server_default=""),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
            sa.Column("idempotency_key", sa.String(255), nullable=False),
            sa.Column("provider_message_id", sa.String(255), nullable=False, server_default=""),
            sa.Column("error", sa.Text(), nullable=False, server_default=""),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.UniqueConstraint("idempotency_key", name="uq_outbound_messages_idempotency_key"),
        )
        op.create_index("ix_outbound_messages_lead_id", "outbound_messages", ["lead_id"])
        op.create_index("ix_outbound_messages_campaign_id", "outbound_messages", ["campaign_id"])
        op.create_index("ix_outbound_messages_account_id", "outbound_messages", ["account_id"])
        op.create_index("ix_outbound_messages_channel", "outbound_messages", ["channel"])
        op.create_index("ix_outbound_messages_status", "outbound_messages", ["status"])

    if "rate_limit_buckets" not in tables:
        op.create_table(
            "rate_limit_buckets",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provider", sa.String(80), nullable=False),
            sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.UniqueConstraint("provider", "window_start", name="uq_rate_limit_provider_window"),
        )
        op.create_index("ix_rate_limit_buckets_provider", "rate_limit_buckets", ["provider"])
        op.create_index("ix_rate_limit_buckets_window_start", "rate_limit_buckets", ["window_start"])


def downgrade() -> None:
    op.drop_table("rate_limit_buckets")
    op.drop_table("outbound_messages")