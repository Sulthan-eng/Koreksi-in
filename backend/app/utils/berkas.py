import uuid
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import settings

REL_PREFIX = "uploads"


def hitung_halaman(konten: bytes, ext: str) -> int:
    """Jumlah halaman berkas. Gambar selalu 1 halaman."""
    if ext != "pdf":
        return 1
    return len(PdfReader(BytesIO(konten)).pages)


def direktori_batch(id_batch: uuid.UUID) -> Path:
    """Direktori fisik tempat berkas jawaban satu batch tersimpan di bawah
    UPLOAD_DIR, mengikuti path relatif `uploads/<id_batch>` (SPEC bagian 5)."""
    return Path(settings.UPLOAD_DIR) / REL_PREFIX / str(id_batch)
