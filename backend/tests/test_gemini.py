from datetime import datetime as real_datetime
from datetime import time, timedelta

import pytest
from google.genai import errors as genai_errors

from app.core.config import settings
from app.services import gemini


@pytest.fixture(autouse=True)
def _anggaran_bersih():
    gemini._anggaran._hitung = {}
    gemini._anggaran._tanggal = None
    gemini._client = None
    yield
    gemini._anggaran._hitung = {}
    gemini._anggaran._tanggal = None
    gemini._client = None


def _patch_sleep(monkeypatch) -> list[int]:
    sleeps: list[int] = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(gemini.asyncio, "sleep", fake_sleep)
    return sleeps


async def test_retry_hanya_untuk_error_sementara(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        if len(calls) == 1:
            raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    hasil = await gemini.ocr_grup([], [])
    assert len(calls) == 2
    assert sleeps == [10]
    assert hasil.items == []


async def test_timeout_dianggap_sementara(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        if len(calls) == 1:
            raise TimeoutError()
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    await gemini.ocr_grup([], [])
    assert len(calls) == 2
    assert sleeps == [10]


async def test_tanpa_retry_untuk_429_kuota_harian_ambigu(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        raise genai_errors.ClientError(429, {"error": {"message": "Resource has been exhausted"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 1
    assert sleeps == []


async def test_retry_untuk_429_per_menit(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        if len(calls) == 1:
            raise genai_errors.ClientError(
                429, {"error": {"message": "Rate limit exceeded, retry per minute"}}
            )
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    await gemini.ocr_grup([], [])
    assert len(calls) == 2
    assert sleeps == [10]


async def test_retry_habis_setelah_3_kali(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.GagalSementara):
        await gemini.ocr_grup([], [])
    assert len(calls) == 4
    assert sleeps == [10, 30, 60]


async def test_error_lain_dianggap_permanen(monkeypatch):
    async def fake_ocr(bagian_file, no_soal_list):
        raise ValueError("respons tidak terduga")

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.GagalPermanen):
        await gemini.ocr_grup([], [])
    assert sleeps == []


async def test_anggaran_bertambah_per_panggilan(monkeypatch):
    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 2


async def test_anggaran_berhenti_tepat_limit(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 1)
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 1


async def test_anggaran_reset_pergantian_hari(monkeypatch):
    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 1

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    besok = hari_ini + timedelta(days=1)

    class _DatetimePalsu:
        @staticmethod
        def now(tz):
            return real_datetime.combine(besok, time(12, 0), tzinfo=tz)

    monkeypatch.setattr(gemini, "datetime", _DatetimePalsu)

    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 1


def test_timeout_eksplisit_120_detik():
    client = gemini._ambil_client()
    assert client._api_client._http_options.timeout == gemini._TIMEOUT_MS
    assert gemini._TIMEOUT_MS == 120_000
