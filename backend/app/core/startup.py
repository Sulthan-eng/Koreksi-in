from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StatusProses
from app.models.file_jawaban import FileJawaban

PESAN_SERVER_DIMULAI_ULANG = "Pemrosesan terhenti karena server dimulai ulang."


async def sapu_proses_tergantung(db: AsyncSession) -> None:
    """File_Jawaban yang masih diproses saat server mati dianggap gagal (SPEC bagian 8)."""
    await db.execute(
        update(FileJawaban)
        .where(FileJawaban.status_proses == StatusProses.DIPROSES)
        .values(status_proses=StatusProses.GAGAL, pesan_error=PESAN_SERVER_DIMULAI_ULANG)
    )
    await db.commit()
