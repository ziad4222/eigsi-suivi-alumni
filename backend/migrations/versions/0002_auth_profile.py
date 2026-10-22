"""Identité, données professionnelles et sessions révocables."""

import sqlalchemy as sa
from alembic import op

revision = "0002_auth_profile"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # The original migration builds metadata dynamically; check columns for fresh installs.
    bind = op.get_bind()
    columns = {c["name"] for c in sa.inspect(bind).get_columns("alumni_profiles")}
    for name, type_, default in [
        ("full_name", sa.String(160), ""),
        ("company", sa.String(160), ""),
        ("sector", sa.String(120), ""),
        ("mentor", sa.Boolean(), "false"),
        ("duplicate_checked", sa.Boolean(), "false"),
    ]:
        if name not in columns:
            op.add_column("alumni_profiles", sa.Column(name, type_, nullable=False, server_default=default))
    from app.models import AuthSession, Campaign

    AuthSession.__table__.create(bind=bind, checkfirst=True)
    Campaign.__table__.create(bind=bind, checkfirst=True)


def downgrade():
    op.drop_table("campaigns")
    op.drop_table("auth_sessions")
    for name in ["duplicate_checked", "mentor", "sector", "company", "full_name"]:
        op.drop_column("alumni_profiles", name)
