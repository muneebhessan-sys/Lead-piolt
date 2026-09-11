"""foundation tables

Revision ID: 0001_foundation
Revises:
Create Date: 2026-09-05
"""
from alembic import op
import sqlalchemy as sa
revision='0001_foundation'; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    op.create_table('search_jobs',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('niche',sa.String(200),nullable=False),sa.Column('location',sa.String(200),nullable=False),sa.Column('status',sa.String(30),nullable=False),sa.Column('target_count',sa.Integer(),nullable=False),sa.Column('processed_count',sa.Integer(),nullable=False),sa.Column('error',sa.Text(),nullable=True),sa.Column('created_at',sa.DateTime(),server_default=sa.text('CURRENT_TIMESTAMP'),nullable=False))
    op.create_table('businesses',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('google_place_id',sa.String(255),unique=True,nullable=True),sa.Column('business_name',sa.String(500),nullable=False),sa.Column('address',sa.Text(),nullable=True),sa.Column('website',sa.Text(),nullable=True),sa.Column('phone',sa.String(80),nullable=True),sa.Column('contact_status',sa.String(30),nullable=False),sa.Column('created_at',sa.DateTime(),server_default=sa.text('CURRENT_TIMESTAMP'),nullable=False))
def downgrade(): op.drop_table('businesses'); op.drop_table('search_jobs')
