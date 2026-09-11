"""store the selected owner sender account on campaigns"""
from alembic import op
import sqlalchemy as sa

revision = "0009_campaign_sender_account"
down_revision = "0008_business_location_social_profiles"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("campaigns", sa.Column("sender_account", sa.String(320), nullable=False, server_default=""))

def downgrade():
    op.drop_column("campaigns", "sender_account")