"""persist safe application audit events"""
from alembic import op
import sqlalchemy as sa
revision='0005_audit_logs'; down_revision='0004_google_business_fields'; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('audit_logs',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('action',sa.String(120),nullable=False),sa.Column('subsystem',sa.String(80),nullable=False),sa.Column('result',sa.String(40),nullable=False),sa.Column('request_id',sa.String(64),nullable=False),sa.Column('safe_error',sa.Text(),nullable=False),sa.Column('created_at',sa.DateTime(),server_default=sa.text('CURRENT_TIMESTAMP'),nullable=False));op.create_index('ix_audit_logs_action','audit_logs',['action']);op.create_index('ix_audit_logs_subsystem','audit_logs',['subsystem']);op.create_index('ix_audit_logs_request_id','audit_logs',['request_id']);op.create_index('ix_audit_logs_created_at','audit_logs',['created_at'])
def downgrade():
    op.drop_index('ix_audit_logs_created_at');op.drop_index('ix_audit_logs_request_id');op.drop_index('ix_audit_logs_subsystem');op.drop_index('ix_audit_logs_action');op.drop_table('audit_logs')
