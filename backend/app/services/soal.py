import uuid

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.batch import Batch
from app.models.enums import StatusBatch
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import gemini
from app.services.batch import BATCH_SUDAH_SELESAI, ambil_batch
from app.services.file_jawaban import TIDAK_ADA_FILE, baca_dan_validasi_file

_MAKS_SOAL_PER_BATCH = 15
_MAKS_PERCOBAAN_NO_SOAL = 5

KUNCI_KOSONG = AppError(
    kode="KUNCI_KOSONG", pesan="Kunci jawaban tidak boleh kosong", status_code=400
)
BATAS_SOAL_TERLAMPAUI = AppError(
    kode="BATAS_SOAL_TERLAMPAUI",
    pesan=f"Maksimal {_MAKS_SOAL_PER_BATCH} soal per batch.",
    status_code=400,
)
SOAL_SETELAH_JAWABAN = AppError(
    kode="SOAL_SETELAH_JAWABAN",
    pesan="Soal tidak dapat ditambah setelah jawaban diunggah.",
    status_code=400,
)
GAGAL_TAMBAH_SOAL = AppError(
    kode="GAGAL_TAMBAH_SOAL", pesan="Gagal menambah soal, silakan coba lagi.", status_code=500
)
OCR_KUNCI_GAGAL = AppError(
    kode="OCR_KUNCI_GAGAL",
    pesan="Gagal membaca file, silakan coba lagi atau masukkan teks secara manual",
    status_code=500,
)


async def pastikan_bisa_tambah_soal(db: AsyncSession, batch: Batch) -> None:
    """Pemeriksaan bersama sebelum menambah soal, baik lewat ketik (tambah_soal)
    maupun lewat OCR file (ocr_kunci, F-KUNCI-FILE): batch Aktif, belum ada
    jawaban, dan belum mencapai batas soal."""
    if batch.status == StatusBatch.SELESAI:
        raise BATCH_SUDAH_SELESAI

    ada_file = await db.scalar(
        select(FileJawaban.id_file).where(FileJawaban.id_batch == batch.id_batch).limit(1)
    )
    if ada_file is not None:
        raise SOAL_SETELAH_JAWABAN

    jumlah_soal = await db.scalar(
        select(func.count()).select_from(Soal).where(Soal.id_batch == batch.id_batch)
    )
    if jumlah_soal >= _MAKS_SOAL_PER_BATCH:
        raise BATAS_SOAL_TERLAMPAUI


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
    await pastikan_bisa_tambah_soal(db, batch)

    kunci = kunci_jawaban.strip()
    if not kunci:
        raise KUNCI_KOSONG

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


async def ocr_kunci(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID, file: UploadFile | None
) -> str:
    """OCR satu file kunci jawaban (F-KUNCI-FILE). Stateless: file tidak pernah
    ditulis ke UPLOAD_DIR atau database, hanya diproses lalu dibuang. Tidak
    menyentuh tabel Soal."""
    batch = await ambil_batch(db, pengguna, id_batch)
    await pastikan_bisa_tambah_soal(db, batch)

    if file is None:
        raise TIDAK_ADA_FILE

    konten, ext = await baca_dan_validasi_file(file)

    try:
        teks = await gemini.ocr_kunci(konten, ext)
    except (gemini.KuotaHarianHabis, gemini.GagalSementara, gemini.GagalPermanen):
        raise OCR_KUNCI_GAGAL from None

    if not teks.strip() or gemini.PENANDA_TIDAK_ADA_TEKS in teks:
        raise OCR_KUNCI_GAGAL

    return teks
