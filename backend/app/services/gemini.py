"""Satu-satunya modul yang mengimpor google-genai (SPEC bagian 8).

Memuat: fungsi OCR grup, fungsi judge grup, semaphore (maks 2 panggilan
paralel), retry (hanya untuk error sementara), dan penghitung anggaran
harian in-memory (zona America/Los_Angeles).
"""

import asyncio
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

_MODEL = "gemini-3.5-flash-lite"
_TZ_LA = ZoneInfo("America/Los_Angeles")
_SEM = asyncio.Semaphore(2)
_RETRY_DELAYS = (10, 30, 60)
_TIMEOUT_MS = 120_000

_MIME_PER_EXT = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
}

_client: genai.Client | None = None


def _ambil_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=_TIMEOUT_MS),
        )
    return _client


class KuotaHarianHabis(Exception):
    """RPD lokal habis, atau error 429 yang tidak dapat dibedakan dari kuota harian. Tanpa retry."""


class GagalSementara(Exception):
    """429 per-menit, 503, atau timeout, setelah retry habis."""


class GagalPermanen(Exception):
    """Kegagalan lain yang bukan masalah kuota/sementara."""


class _Anggaran:
    def __init__(self) -> None:
        self._tanggal: date | None = None
        self._hitung: dict[str, int] = {}

    def _reset_jika_hari_baru(self) -> None:
        hari_ini = datetime.now(_TZ_LA).date()
        if hari_ini != self._tanggal:
            self._tanggal = hari_ini
            self._hitung = {}

    def boleh_panggil(self, model: str) -> bool:
        self._reset_jika_hari_baru()
        return self._hitung.get(model, 0) < settings.GEMINI_RPD_LIMIT

    def catat(self, model: str) -> int:
        self._reset_jika_hari_baru()
        self._hitung[model] = self._hitung.get(model, 0) + 1
        return self._hitung[model]


_anggaran = _Anggaran()


# --- Skema structured output ---
# id_item berbentuk "{file_index}:{no_soal}", dikembalikan model apa adanya
# agar hasil bisa dipetakan balik tanpa mengandalkan urutan list.


class HasilOcrItem(BaseModel):
    id_item: str
    teks: str


class ResponsOcr(BaseModel):
    items: list[HasilOcrItem]


class ItemJudgeMasuk(BaseModel):
    id_item: str
    kunci_jawaban: str
    teks_jawaban: str


class HasilJudgeItem(BaseModel):
    id_item: str
    skor: int


class ResponsJudge(BaseModel):
    items: list[HasilJudgeItem]


def _prompt_ocr(no_soal_list: list[int]) -> str:
    daftar = ", ".join(str(n) for n in no_soal_list)
    return (
        "Baca lembar jawaban berikut dan ekstrak teks jawaban untuk setiap nomor soal. "
        f"Nomor soal yang ADA pada batch ini hanyalah: {daftar}. "
        "Untuk setiap berkas (file_index diberikan per berkas) dan setiap nomor soal yang "
        "jawabannya ditemukan pada berkas itu, kembalikan satu item dengan id_item berformat "
        '"{file_index}:{no_soal}" dan teks jawaban apa adanya. '
        "JANGAN menebak nomor soal. Jika sebuah lembar tidak bernomor atau nomor tidak dapat "
        "dipastikan, JANGAN masukkan item untuk nomor itu. Jangan mengembalikan nomor soal di "
        "luar daftar yang diberikan."
    )


def _prompt_judge() -> str:
    return (
        "Nilai kemiripan tiap jawaban peserta didik terhadap kunci jawaban, dengan skala "
        "0 sampai 100: 0 untuk jawaban salah; 1 sampai 39 untuk sebagian kecil benar; "
        "40 sampai 79 untuk sebagian benar; 80 sampai 100 untuk benar. "
        "Nilai HANYA kebenaran isi jawaban, bukan gaya penulisan, ejaan, atau kesalahan baca "
        "OCR yang kecil. Untuk setiap item, kembalikan id_item apa adanya dan skor integer. "
        "Jangan menyertakan alasan."
    )


async def _panggil_sdk_ocr(
    bagian_file: list[tuple[bytes, str, int]], no_soal_list: list[int]
) -> ResponsOcr:
    """Satu-satunya titik yang memanggil SDK untuk OCR grup. bagian_file: list of
    (konten, ext, file_index)."""
    client = _ambil_client()
    parts: list[types.Part] = [types.Part.from_text(text=_prompt_ocr(no_soal_list))]
    for konten, ext, file_index in bagian_file:
        parts.append(types.Part.from_text(text=f"Berkas file_index={file_index}:"))
        parts.append(types.Part.from_bytes(data=konten, mime_type=_MIME_PER_EXT[ext]))
    response = await client.aio.models.generate_content(
        model=_MODEL,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResponsOcr,
        ),
    )
    return ResponsOcr.model_validate_json(response.text)


async def _panggil_sdk_judge(items: list[ItemJudgeMasuk]) -> ResponsJudge:
    """Satu-satunya titik yang memanggil SDK untuk judge grup."""
    client = _ambil_client()
    daftar_item = "\n".join(
        f"id_item={i.id_item}\nkunci_jawaban={i.kunci_jawaban}\nteks_jawaban={i.teks_jawaban}"
        for i in items
    )
    response = await client.aio.models.generate_content(
        model=_MODEL,
        contents=[_prompt_judge(), daftar_item],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResponsJudge,
        ),
    )
    return ResponsJudge.model_validate_json(response.text)


def _klasifikasikan(exc: Exception) -> str:
    """503/timeout -> transient. 429 -> cek teks pesan untuk indikasi per-menit/rate;
    jika tidak jelas -> kuota_harian (tanpa retry, sesuai aturan 'default ke yang lebih aman').
    Selainnya -> permanen."""
    if isinstance(exc, genai_errors.ServerError):
        return "transient"
    if isinstance(exc, TimeoutError | asyncio.TimeoutError):
        return "transient"
    if isinstance(exc, genai_errors.ClientError) and getattr(exc, "code", None) == 429:
        pesan = f"{getattr(exc, 'message', '') or ''} {getattr(exc, 'details', '') or ''}".lower()
        pesan_rapat = pesan.replace(" ", "").replace("_", "")
        ada_per_menit = "perminute" in pesan_rapat
        ada_per_hari = "perday" in pesan_rapat
        if ada_per_menit and not ada_per_hari:
            return "transient"
        return "kuota_harian"
    return "permanen"


async def _dengan_retry_dan_anggaran(model: str, jumlah_item: int, fn) -> ResponsOcr | ResponsJudge:
    if not _anggaran.boleh_panggil(model):
        logger.info("gemini_call_skipped model=%s items=%d reason=rpd_habis", model, jumlah_item)
        raise KuotaHarianHabis()

    percobaan = 0
    while True:
        delay: int | None = None
        async with _SEM:
            hitung_hari_ini = _anggaran.catat(model)
            logger.info(
                "gemini_call model=%s items=%d daily_count=%d attempt=%d",
                model,
                jumlah_item,
                hitung_hari_ini,
                percobaan + 1,
            )
            try:
                return await fn()
            except Exception as exc:
                klasifikasi = _klasifikasikan(exc)
                if klasifikasi == "kuota_harian":
                    raise KuotaHarianHabis() from exc
                if klasifikasi == "permanen":
                    raise GagalPermanen() from exc
                if percobaan >= len(_RETRY_DELAYS):
                    raise GagalSementara() from exc
                delay = _RETRY_DELAYS[percobaan]

        await asyncio.sleep(delay)
        percobaan += 1


async def ocr_grup(
    bagian_file: list[tuple[bytes, str, int]], no_soal_list: list[int]
) -> ResponsOcr:
    return await _dengan_retry_dan_anggaran(
        _MODEL, len(bagian_file), lambda: _panggil_sdk_ocr(bagian_file, no_soal_list)
    )


async def judge_grup(items: list[ItemJudgeMasuk]) -> ResponsJudge:
    return await _dengan_retry_dan_anggaran(_MODEL, len(items), lambda: _panggil_sdk_judge(items))
