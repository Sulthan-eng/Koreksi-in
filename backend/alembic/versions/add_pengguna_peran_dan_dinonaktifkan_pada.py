"""add Pengguna peran dan dinonaktifkan_pada columns

Revision ID: e8f3g5h6i7j8
Revises: d7e2c4f91a63
Create Date: 2026-11-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f3g5h6i7j8"
down_revision: str | None = "d7e2c4f91a63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    peran_enum = postgresql.ENUM("pengajar", "admin", name="peran")
    bind = op.get_bind()
    peran_enum.create(bind, checkfirst=True)
    op.add_column(
        "Pengguna",
        sa.Column(
            "peran",
            postgresql.ENUM("pengajar", "admin", name="peran", create_type=False),
            server_default="pengajar",
            nullable=False,
        ),
    )
    op.add_column(
        "Pengguna", sa.Column("dinonaktifkan_pada", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("Pengguna", "dinonaktifkan_pada")
    op.drop_column("Pengguna", "peran")
    peran_enum = postgresql.ENUM("pengajar", "admin", name="peran")
    peran_enum.drop(op.get_bind(), checkfirst=True)
