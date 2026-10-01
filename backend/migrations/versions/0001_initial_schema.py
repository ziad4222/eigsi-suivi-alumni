"""Schéma initial du MVP Alumni."""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    from app import models  # noqa: F401
    from app.database import Base

    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    from app.database import Base

    Base.metadata.drop_all(bind=bind)
