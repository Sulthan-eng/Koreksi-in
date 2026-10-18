import uuid

from pydantic import BaseModel

from app.models.enums import Kategori


class HasilKoreksiItem(BaseModel):
    id_file: uuid.UUID
    nama_peserta_didik: str
    no_soal: int
    teks_ocr: str
    skor_sistem: int | None
    kategori: Kategori | None
