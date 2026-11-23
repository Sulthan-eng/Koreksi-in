"""create Transaksi_Pembayaran table

Revision ID: f1a2b3c4d5e6
Revises: e8f3g5h6i7j8
Create Date: 2026-11-23 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e8f3g5h6i7j8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

paket_langganan_enum = postgresql.ENUM("pro_1_bulan", "pro_3_bulan", name="paket_langganan")
status_transaksi_enum = postgresql.ENUM(
    "menunggu", "berhasil", "gagal", "kedaluwarsa", name="status_transaksi"
)


def upgrade() -> None:
    bind = op.get_bind()
    paket_langganan_enum.create(bind, checkfirst=True)
    status_transaksi_enum.create(bind, checkfirst=True)

    op.create_table(
        "Transaksi_Pembayaran",
        sa.Column("id_transaksi", sa.Uuid(), nullable=False),
        sa.Column("id_pengguna", sa.Uuid(), nullable=False),
        sa.Column("id_order", sa.String(length=50), nullable=False),
        sa.Column(
            "paket",
            postgresql.ENUM(
                "pro_1_bulan", "pro_3_bulan", name="paket_langganan", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("nominal", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "menunggu",
                "berhasil",
                "gagal",
                "kedaluwarsa",
                name="status_transaksi",
                create_type=False,
            ),
            server_default="menunggu",
            nullable=False,
        ),
        sa.Column("diperbarui_pada", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "dibuat_pada",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["id_pengguna"], ["Pengguna.id_pengguna"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_transaksi"),
        sa.UniqueConstraint("id_order"),
    )
    op.create_index("ix_transaksi_pembayaran_id_pengguna", "Transaksi_Pembayaran", ["id_pengguna"])


def downgrade() -> None:
    op.drop_index("ix_transaksi_pembayaran_id_pengguna", table_name="Transaksi_Pembayaran")
    op.drop_table("Transaksi_Pembayaran")
    status_transaksi_enum.drop(op.get_bind(), checkfirst=True)
    paket_langganan_enum.drop(op.get_bind(), checkfirst=True)
