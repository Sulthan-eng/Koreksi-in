import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services.batch import ambil_batch

KUNCI_KOSONG = AppError(
    kode="KUNCI_KOSONG", pesan="Kunci jawaban tidak boleh kosong", status_code=400
)
BATAS_SOAL_TERLAMPAUI = AppError(
    kode="BATAS_SOAL_TERLAMPAUI", pesan="Maksimal 20 soal per batch.", status_code=400
)
SOAL_SETELAH_JAWABAN = AppError(
    kode="SOAL_SETELAH_JAWABAN",
    pesan="Soal tidak dapat ditambah setelah jawaban diunggah.",
    status_code=400,
)
GAGAL_TAMBAH_SOAL = AppError(
    kode="GAGAL_TAMBAH_SOAL", pesan="Gagal menambah soal, silakan coba lagi.", status_code=500
)

_MAKS_SOAL_PER_BATCH = 20
_MAKS_PERCOBAAN_NO_SOAL = 5


async def daftar_soal(db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID) -> list[Soal]:
    batch = await ambil_batch(db, pengguna, id_batch)
    hasil = await db.scalars(
        select(Soal).where(Soal.id_batch == batch.id_batch).order_by(Soal.no_soal)
    )
    return list(hasil)


async def tambah_soal(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID, kunci_jawaban: str
) -> Soal:
    batch = await ambil_batch(db, pengguna, id_batch)

    kunci = kunci_jawaban.strip()
    if not kunci:
        raise KUNCI_KOSONG

    ada_file = await db.scalar(
        select(FileJawaban.id_file).where(FileJawaban.id_batch == batch.id_batch).limit(1)
    )
    if ada_file is not None:
        raise SOAL_SETELAH_JAWABAN

    for _ in range(_MAKS_PERCOBAAN_NO_SOAL):
        jumlah_soal = await db.scalar(
            select(func.count()).select_from(Soal).where(Soal.id_batch == batch.id_batch)
        )
        if jumlah_soal >= _MAKS_SOAL_PER_BATCH:
            raise BATAS_SOAL_TERLAMPAUI

        no_soal_tertinggi = await db.scalar(
            select(func.max(Soal.no_soal)).where(Soal.id_batch == batch.id_batch)
        )
        soal = Soal(
            id_batch=batch.id_batch,
            no_soal=(no_soal_tertinggi or 0) + 1,
            kunci_jawaban=kunci,
        )
        db.add(soal)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        return soal

    raise GAGAL_TAMBAH_SOAL
