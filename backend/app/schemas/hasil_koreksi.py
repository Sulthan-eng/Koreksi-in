import uuid
from typing import Any

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
    skor_revisi: int | None
    skor_hitung_ulang: bool


class EditTeksOcrRequest(BaseModel):
    teks_ocr: str


class HasilKoreksiEditResponse(BaseModel):
    id_koreksi: uuid.UUID
    teks_ocr: str
    skor_sistem: int | None
    kategori: Kategori | None
    skor_hitung_ulang: bool


class UbahNilaiAkhirRequest(BaseModel):
    """Nilai mentah, tanpa validasi tipe/rentang di skema — divalidasi penuh di
    services.hasil_koreksi.ubah_nilai_akhir supaya nilai tidak valid mengembalikan
    400 NILAI_AKHIR_TIDAK_VALID, bukan 422 VALIDASI_GAGAL generik."""

    skor_revisi: Any


class HasilKoreksiNilaiResponse(BaseModel):
    id_koreksi: uuid.UUID
    skor_revisi: int
