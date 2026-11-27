"""add Pengguna percobaan password gagal columns

Revision ID: b4c6d8e0f1a3
Revises: a1b2c3d4e5f7
Create Date: 2026-11-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4c6d8e0f1a3"
down_revision: str | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "Pengguna",
        sa.Column("percobaan_password_gagal", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "Pengguna",
        sa.Column("percobaan_terkunci_sampai", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("Pengguna", "percobaan_terkunci_sampai")
    op.drop_column("Pengguna", "percobaan_password_gagal")
