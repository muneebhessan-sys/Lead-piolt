"""add official Google Places business fields"""
from alembic import op
import sqlalchemy as sa
revision='0004_google_business_fields'; down_revision='0003_core_leads'; branch_labels=None; depends_on=None
def upgrade():
    op.add_column('businesses',sa.Column('category',sa.String(200)));op.add_column('businesses',sa.Column('categories',sa.Text(),server_default='[]',nullable=False));op.add_column('businesses',sa.Column('latitude',sa.String(40)));op.add_column('businesses',sa.Column('longitude',sa.String(40)));op.add_column('businesses',sa.Column('rating',sa.String(20)));op.add_column('businesses',sa.Column('review_count',sa.Integer()));op.add_column('businesses',sa.Column('business_status',sa.String(80)));op.add_column('businesses',sa.Column('google_maps_url',sa.Text()))
def downgrade():
    with op.batch_alter_table('businesses') as batch:
        batch.drop_column('google_maps_url');batch.drop_column('business_status');batch.drop_column('review_count');batch.drop_column('rating');batch.drop_column('longitude');batch.drop_column('latitude');batch.drop_column('categories');batch.drop_column('category')
