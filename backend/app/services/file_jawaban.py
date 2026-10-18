import uuid
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.models.enums import StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services.batch import ambil_batch

BELUM_ADA_SOAL = AppError(
    kode="BELUM_ADA_SOAL",
    pesan="Tambahkan minimal satu soal sebelum mengunggah jawaban.",
    status_code=400,
)
TIDAK_ADA_FILE = AppError(
    kode="TIDAK_ADA_FILE", pesan="Pilih minimal satu file untuk diunggah.", status_code=400
)
MAKS_FILE_TERLAMPAUI = AppError(
    kode="MAKS_FILE_TERLAMPAUI", pesan="Maksimal 10 file per unggahan.", status_code=400
)
NAMA_PESERTA_KOSONG = AppError(
    kode="NAMA_PESERTA_KOSONG",
    pesan="Nama peserta didik wajib untuk semua file",
    status_code=400,
)
NAMA_PESERTA_TERLALU_PANJANG = AppError(
    kode="NAMA_PESERTA_TERLALU_PANJANG",
    pesan="Nama peserta didik maksimal 100 karakter.",
    status_code=400,
)
FORMAT_FILE_TIDAK_DIDUKUNG = AppError(
    kode="FORMAT_FILE_TIDAK_DIDUKUNG",
    pesan="Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
    status_code=400,
)
FILE_TERLALU_BESAR = AppError(
    kode="FILE_TERLALU_BESAR", pesan="Ukuran file maksimal 10 MB.", status_code=400
)
PDF_TERLALU_BANYAK_HALAMAN = AppError(
    kode="PDF_TERLALU_BANYAK_HALAMAN", pesan="PDF maksimal 15 halaman.", status_code=400
)
PDF_TIDAK_DAPAT_DIBACA = AppError(
    kode="PDF_TIDAK_DAPAT_DIBACA",
    pesan="File PDF rusak atau tidak dapat dibaca.",
    status_code=400,
)
GAGAL_SIMPAN_JAWABAN = AppError(
    kode="GAGAL_SIMPAN_JAWABAN",
    pesan="Gagal menyimpan jawaban, silakan coba lagi.",
    status_code=500,
)

_MAKS_FILE_PER_UNGGAHAN = 10
_MAKS_PANJANG_NAMA = 100
_MAKS_UKURAN_BYTE = 10 * 1024 * 1024
_MAKS_HALAMAN_PDF = 15
_UKURAN_CHUNK = 1024 * 1024
_REL_PREFIX = "uploads"

_SIGNATURE_PDF = b"%PDF-"
_SIGNATURE_PNG = b"\x89PNG\r\n\x1a\n"
_SIGNATURE_JPEG = b"\xff\xd8\xff"


async def _baca_dengan_batas(file: UploadFile) -> bytes:
    """Baca bertahap per chunk, berhenti sedini mungkin begitu melebihi batas ukuran."""
    buffer = BytesIO()
    total = 0
    while True:
        potongan = await file.read(_UKURAN_CHUNK)
        if not potongan:
            break
        total += len(potongan)
        if total > _MAKS_UKURAN_BYTE:
            raise FILE_TERLALU_BESAR
        buffer.write(potongan)
    return buffer.getvalue()


def _deteksi_format(konten: bytes) -> str:
    if konten.startswith(_SIGNATURE_PDF):
        return "pdf"
    if konten.startswith(_SIGNATURE_PNG):
        return "png"
    if konten.startswith(_SIGNATURE_JPEG):
        return "jpg"
    raise FORMAT_FILE_TIDAK_DIDUKUNG


def _hitung_halaman_pdf(konten: bytes) -> int:
    try:
        return len(PdfReader(BytesIO(konten)).pages)
    except Exception:
        raise PDF_TIDAK_DAPAT_DIBACA from None


def _rel_path(id_batch: uuid.UUID, id_file: uuid.UUID, ext: str) -> str:
    return f"{_REL_PREFIX}/{id_batch}/{id_file}.{ext}"


async def daftar_file_jawaban(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID
) -> list[FileJawaban]:
    batch = await ambil_batch(db, pengguna, id_batch)
    hasil = await db.scalars(
        select(FileJawaban)
        .where(FileJawaban.id_batch == batch.id_batch)
        .order_by(FileJawaban.diunggah_pada)
    )
    return list(hasil)


async def unggah_jawaban(
    db: AsyncSession,
    pengguna: Pengguna,
    id_batch: uuid.UUID,
    files: list[UploadFile],
    nama_peserta_didik: list[str],
) -> list[FileJawaban]:
    batch = await ambil_batch(db, pengguna, id_batch)

    ada_soal = await db.scalar(select(Soal.id_soal).where(Soal.id_batch == batch.id_batch).limit(1))
    if ada_soal is None:
        raise BELUM_ADA_SOAL

    if len(files) == 0:
        raise TIDAK_ADA_FILE
    if len(files) > _MAKS_FILE_PER_UNGGAHAN:
        raise MAKS_FILE_TERLAMPAUI
    if len(nama_peserta_didik) != len(files):
        raise AppError(
            kode="VALIDASI_GAGAL", pesan="Data yang dikirim tidak valid.", status_code=422
        )

    nama_tervalidasi: list[str] = []
    for nama in nama_peserta_didik:
        nama_bersih = nama.strip()
        if not nama_bersih:
            raise NAMA_PESERTA_KOSONG
        if len(nama_bersih) > _MAKS_PANJANG_NAMA:
            raise NAMA_PESERTA_TERLALU_PANJANG
        nama_tervalidasi.append(nama_bersih)

    item_tervalidasi: list[tuple[bytes, str]] = []
    for file in files:
        konten = await _baca_dengan_batas(file)
        ext = _deteksi_format(konten)
        if ext == "pdf":
            jumlah_halaman = _hitung_halaman_pdf(konten)
            if jumlah_halaman > _MAKS_HALAMAN_PDF:
                raise PDF_TERLALU_BANYAK_HALAMAN
        item_tervalidasi.append((konten, ext))

    basis = datetime.now(UTC)
    path_tertulis: list[Path] = []
    baris_baru: list[FileJawaban] = []
    try:
        for i, ((konten, ext), nama_bersih) in enumerate(
            zip(item_tervalidasi, nama_tervalidasi, strict=True)
        ):
            id_file = uuid.uuid4()
            rel_path = _rel_path(batch.id_batch, id_file, ext)
            full_path = Path(settings.UPLOAD_DIR) / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(konten)
            path_tertulis.append(full_path)

            baris_baru.append(
                FileJawaban(
                    id_file=id_file,
                    id_batch=batch.id_batch,
                    nama_peserta_didik=nama_bersih,
                    path=rel_path,
                    status_proses=StatusProses.DIPROSES,
                    diunggah_pada=basis + timedelta(microseconds=i),
                )
            )
        db.add_all(baris_baru)
        await db.commit()
    except (OSError, SQLAlchemyError):
        await db.rollback()
        for path in path_tertulis:
            path.unlink(missing_ok=True)
        raise GAGAL_SIMPAN_JAWABAN from None

    return baris_baru
