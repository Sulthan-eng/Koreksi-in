"""add Pengguna reset password columns

Revision ID: d7e2c4f91a63
Revises: 4c9f6a1d8b2e
Create Date: 2026-11-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7e2c4f91a63"
down_revision: str | None = "4c9f6a1d8b2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("Pengguna", sa.Column("reset_token_hash", sa.String(length=64), nullable=True))
    op.add_column(
        "Pengguna", sa.Column("reset_dibuat_pada", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_unique_constraint(None, "Pengguna", ["reset_token_hash"])


def downgrade() -> None:
    op.drop_column("Pengguna", "reset_dibuat_pada")
    op.drop_column("Pengguna", "reset_token_hash")
