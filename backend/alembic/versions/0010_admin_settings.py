"""add admin settings table for persisted control-center configuration"""

from alembic import op
import sqlalchemy as sa

revision = "0010_admin_settings"
down_revision = "0009_campaign_sender_account"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=""),
        sa.Column("protected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(op.f("ix_admin_settings_key"), "admin_settings", ["key"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_admin_settings_key"), table_name="admin_settings")
    op.drop_table("admin_settings")
