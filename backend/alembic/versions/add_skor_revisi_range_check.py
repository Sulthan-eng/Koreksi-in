"""add skor_revisi range check

Revision ID: 4c9f6a1d8b2e
Revises: b3a5def9e430
Create Date: 2026-11-02 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c9f6a1d8b2e"
down_revision: str | None = "b3a5def9e430"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_hasil_koreksi_skor_revisi_range",
        "Hasil_Koreksi",
        "skor_revisi IS NULL OR (skor_revisi >= 0 AND skor_revisi <= 100)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_hasil_koreksi_skor_revisi_range", "Hasil_Koreksi", type_="check")
