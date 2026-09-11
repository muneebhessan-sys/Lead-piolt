"""add normalized business location and social profiles"""
from alembic import op
import sqlalchemy as sa

revision = "0008_business_location_social_profiles"
down_revision = "0007_integration_configuration"
branch_labels = None
depends_on = None

def upgrade():
    for name, length in (("locality", 160), ("city", 160), ("region", 160), ("country", 120)):
        op.add_column("businesses", sa.Column(name, sa.String(length), nullable=True))
    op.create_table(
        "business_social_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False, index=True),
        sa.Column("platform", sa.String(30), nullable=False, index=True),
        sa.Column("profile_url", sa.Text(), nullable=False),
        sa.Column("username", sa.String(160), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(80), nullable=False, server_default="USER_STORED"),
        sa.Column("status", sa.String(30), nullable=False, server_default="STORED"),
        sa.UniqueConstraint("business_id", "platform", "profile_url", name="uq_business_social_profile"),
    )

def downgrade():
    op.drop_table("business_social_profiles")
    for name in ("country", "region", "city", "locality"):
        op.drop_column("businesses", name)