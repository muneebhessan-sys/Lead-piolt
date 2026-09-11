"""store provider configuration server-side"""
from alembic import op
import sqlalchemy as sa

revision = "0007_integration_configuration"
down_revision = "0006_crm_workflows"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("integrations", sa.Column("account_name", sa.String(200), nullable=False, server_default=""))
    op.add_column("integrations", sa.Column("capabilities", sa.Text(), nullable=False, server_default="[]"))
    op.add_column("integrations", sa.Column("secret_value", sa.Text(), nullable=False, server_default=""))
    op.add_column("integrations", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    for column in ("enabled", "secret_value", "capabilities", "account_name"):
        op.drop_column("integrations", column)