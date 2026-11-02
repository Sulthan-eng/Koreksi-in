import logging
import shutil
import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.batch import Batch
from app.models.pengguna import Pengguna
from app.utils.berkas import direktori_batch

logger = logging.getLogger(__name__)

BATCH_TIDAK_DITEMUKAN = AppError(
    kode="BATCH_TIDAK_DITEMUKAN", pesan="Batch tidak ditemukan", status_code=404
)
NAMA_BATCH_KOSONG = AppError(
    kode="NAMA_BATCH_KOSONG", pesan="Nama batch tidak boleh kosong.", status_code=400
)
GAGAL_BUAT_BATCH = AppError(
    kode="GAGAL_BUAT_BATCH", pesan="Gagal membuat batch, silakan coba lagi", status_code=500
)
GAGAL_HAPUS_BATCH = AppError(
    kode="GAGAL_HAPUS_BATCH", pesan="Gagal menghapus batch, silakan coba lagi", status_code=500
)


async def daftar_batch(db: AsyncSession, pengguna: Pengguna) -> list[Batch]:
    hasil = await db.scalars(
        select(Batch)
        .where(Batch.id_pengguna == pengguna.id_pengguna)
        .order_by(Batch.dibuat_pada.desc())
    )
    return list(hasil)


async def buat_batch(db: AsyncSession, pengguna: Pengguna, nama_batch: str) -> Batch:
    nama = nama_batch.strip()
    if not nama:
        raise NAMA_BATCH_KOSONG

    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch=nama)
    db.add(batch)
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_BUAT_BATCH from None
    return batch


async def ambil_batch(db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID) -> Batch:
    batch = await db.scalar(
        select(Batch).where(Batch.id_batch == id_batch, Batch.id_pengguna == pengguna.id_pengguna)
    )
    if batch is None:
        raise BATCH_TIDAK_DITEMUKAN
    return batch


async def hapus_batch(db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID) -> None:
    """Hapus baris database (cascade ke Soal, File_Jawaban, Hasil_Koreksi) lalu
    hapus direktori fisik secara best-effort. Setelah DB commit, data sudah
    pasti terhapus; kegagalan hapus direktori hanya dicatat log, tidak
    dikembalikan sebagai error ke pengguna (tidak ada jalan mundur)."""
    batch = await ambil_batch(db, pengguna, id_batch)
    id_batch_val = batch.id_batch

    try:
        await db.delete(batch)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_HAPUS_BATCH from None

    direktori = direktori_batch(id_batch_val)
    try:
        if direktori.exists():
            shutil.rmtree(direktori)
    except OSError:
        logger.error("hapus_batch_berkas_gagal id_batch=%s", id_batch_val, exc_info=True)
