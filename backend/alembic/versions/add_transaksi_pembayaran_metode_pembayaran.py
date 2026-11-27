"""add Transaksi_Pembayaran metode_pembayaran column

Revision ID: c5d7e9f1a2b4
Revises: b4c6d8e0f1a3
Create Date: 2026-11-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d7e9f1a2b4"
down_revision: str | None = "b4c6d8e0f1a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "Transaksi_Pembayaran",
        sa.Column("metode_pembayaran", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("Transaksi_Pembayaran", "metode_pembayaran")
