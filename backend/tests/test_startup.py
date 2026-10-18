import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.startup import PESAN_SERVER_DIMULAI_ULANG, sapu_proses_tergantung
from app.models.batch import Batch
from app.models.enums import StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna


async def test_sapu_proses_tergantung_menandai_gagal(db_session: AsyncSession) -> None:
    pengguna = Pengguna(nama="Budi", email=f"{uuid.uuid4()}@contoh.com", password_hash="hash")
    db_session.add(pengguna)
    await db_session.commit()

    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch="Batch")
    db_session.add(batch)
    await db_session.commit()

    sedang_diproses = FileJawaban(
        id_batch=batch.id_batch,
        nama_peserta_didik="Budi",
        path=f"uploads/{batch.id_batch}/a.png",
        status_proses=StatusProses.DIPROSES,
    )
    sudah_selesai = FileJawaban(
        id_batch=batch.id_batch,
        nama_peserta_didik="Ani",
        path=f"uploads/{batch.id_batch}/b.png",
        status_proses=StatusProses.SELESAI,
    )
    db_session.add_all([sedang_diproses, sudah_selesai])
    await db_session.commit()

    await sapu_proses_tergantung(db_session)

    await db_session.refresh(sedang_diproses)
    await db_session.refresh(sudah_selesai)
    assert sedang_diproses.status_proses == StatusProses.GAGAL
    assert sedang_diproses.pesan_error == PESAN_SERVER_DIMULAI_ULANG
    assert sudah_selesai.status_proses == StatusProses.SELESAI
    assert sudah_selesai.pesan_error is None
