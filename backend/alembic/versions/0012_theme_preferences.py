"""Add persisted admin theme settings"""

from alembic import op
import sqlalchemy as sa

revision = "0012_theme_preferences"
down_revision = "0011_extended_models"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())
    if "admin_settings" not in existing:
        return

    admin_settings = sa.table(
        "admin_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.String),
        sa.column("protected", sa.Boolean),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    for key, value in {"ui.theme": "OBSIDIAN", "ui.reduced_motion": "false"}.items():
        existing_row = bind.execute(sa.select(admin_settings.c.key).where(admin_settings.c.key == key)).scalar_one_or_none()
        if existing_row is None:
            op.execute(
                admin_settings.insert().values(
                    key=key,
                    value=value,
                    protected=False,
                    created_at=sa.func.now(),
                    updated_at=sa.func.now(),
                )
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "admin_settings" not in set(inspector.get_table_names()):
        return
    op.execute("DELETE FROM admin_settings WHERE key IN ('ui.theme', 'ui.reduced_motion')")
