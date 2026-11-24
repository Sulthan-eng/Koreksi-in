"""create Pemakaian_Gemini table

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-11-24 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f7"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "Pemakaian_Gemini",
        sa.Column("id_pemakaian_gemini", sa.Uuid(), nullable=False),
        sa.Column("tanggal", sa.Date(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("jumlah_panggilan", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id_pemakaian_gemini"),
        sa.UniqueConstraint("tanggal", "model", name="uq_pemakaian_gemini_tanggal_model"),
    )


def downgrade() -> None:
    op.drop_table("Pemakaian_Gemini")
