import uuid

from pydantic import BaseModel

from app.models.enums import Kategori


class HasilKoreksiItem(BaseModel):
    id_koreksi: uuid.UUID
    id_file: uuid.UUID
    nama_peserta_didik: str
    no_soal: int
    teks_ocr: str
    skor_sistem: int | None
    kategori: Kategori | None
    skor_hitung_ulang: bool


class EditTeksOcrRequest(BaseModel):
    teks_ocr: str


class HasilKoreksiEditResponse(BaseModel):
    id_koreksi: uuid.UUID
    teks_ocr: str
    skor_sistem: int | None
    kategori: Kategori | None
    skor_hitung_ulang: bool

