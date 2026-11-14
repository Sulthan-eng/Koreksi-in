from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.enums import StatusBatch, StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.services.langganan import BATAS_PER_JENIS_AKUN, jenis_akun_efektif


@dataclass(frozen=True)
class Ringkasan:
    total_batch: int
    peserta_didik_dikoreksi: int
    sisa_slot_batch_aktif: int | None
    sisa_slot_jawaban_per_batch: int | None


async def ambil_ringkasan(db: AsyncSession, pengguna: Pengguna) -> Ringkasan:
    total_batch = await db.scalar(
        select(func.count()).select_from(Batch).where(Batch.id_pengguna == pengguna.id_pengguna)
    )
    peserta_didik_dikoreksi = await db.scalar(
        select(func.count())
        .select_from(FileJawaban)
        .join(Batch, FileJawaban.id_batch == Batch.id_batch)
        .where(
            Batch.id_pengguna == pengguna.id_pengguna,
            FileJawaban.status_proses == StatusProses.SELESAI,
        )
    )

    jenis = jenis_akun_efektif(pengguna)
    batas = BATAS_PER_JENIS_AKUN[jenis]
    if jenis == StatusLangganan.PRO:
        return Ringkasan(
            total_batch=total_batch,
            peserta_didik_dikoreksi=peserta_didik_dikoreksi,
            sisa_slot_batch_aktif=None,
            sisa_slot_jawaban_per_batch=None,
        )

    jumlah_aktif = await db.scalar(
        select(func.count())
        .select_from(Batch)
        .where(Batch.id_pengguna == pengguna.id_pengguna, Batch.status == StatusBatch.AKTIF)
    )
    sisa_slot_batch_aktif = max(0, batas.maks_batch_aktif - jumlah_aktif)

    id_batch_aktif_terbaru = await db.scalar(
        select(Batch.id_batch)
        .where(Batch.id_pengguna == pengguna.id_pengguna, Batch.status == StatusBatch.AKTIF)
        .order_by(Batch.dibuat_pada.desc(), Batch.id_batch.desc())
        .limit(1)
    )
    if id_batch_aktif_terbaru is None:
        sisa_slot_jawaban_per_batch = batas.maks_jawaban_per_batch
    else:
        jumlah_jawaban = await db.scalar(
            select(func.count())
            .select_from(FileJawaban)
            .where(FileJawaban.id_batch == id_batch_aktif_terbaru)
        )
        sisa_slot_jawaban_per_batch = max(0, batas.maks_jawaban_per_batch - jumlah_jawaban)

    return Ringkasan(
        total_batch=total_batch,
        peserta_didik_dikoreksi=peserta_didik_dikoreksi,
        sisa_slot_batch_aktif=sisa_slot_batch_aktif,
        sisa_slot_jawaban_per_batch=sisa_slot_jawaban_per_batch,
    )
