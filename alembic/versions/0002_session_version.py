"""add session version for logout

Revision ID: 0002_session_version
Revises: 0001_initial_uc001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_session_version"
down_revision = "0001_initial_uc001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("employees") as batch:
        batch.add_column(
            sa.Column(
                "session_version", sa.Integer(), nullable=False, server_default="0"
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("employees") as batch:
        batch.drop_column("session_version")
