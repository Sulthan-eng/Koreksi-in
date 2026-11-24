import asyncio
import uuid
from datetime import datetime as real_datetime
from datetime import time, timedelta

import pytest
import pytest_asyncio
from google.genai import errors as genai_errors
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.pemakaian_gemini import PemakaianGemini
from app.models.pengguna import Pengguna
from app.services import gemini


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _anggaran_bersih(db_session: AsyncSession):
    gemini._anggaran = gemini._Anggaran()
    gemini._client = None
    yield
    gemini._anggaran = gemini._Anggaran()
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


async def test_kuota_harian_pesan_realistis_tanpa_retry(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        raise genai_errors.ClientError(
            429,
            {
                "error": {
                    "message": (
                        "Quota exceeded for quota metric "
                        "'generativelanguage.googleapis.com/generate_content_free_tier_requests' "
                        "and limit 'GenerateRequestsPerDayPerProjectPerModel-FreeTier' "
                        "of service 'generativelanguage.googleapis.com'"
                    )
                }
            },
        )

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 1
    assert sleeps == []


async def test_429_per_menit_pesan_realistis_di_retry(monkeypatch):
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        if len(calls) == 1:
            raise genai_errors.ClientError(
                429,
                {
                    "error": {
                        "message": (
                            "Quota exceeded for quota metric "
                            "'generativelanguage.googleapis.com/"
                            "generate_content_free_tier_requests' "
                            "and limit "
                            "'GenerateRequestsPerMinutePerProjectPerModel-FreeTier' "
                            "of service 'generativelanguage.googleapis.com'"
                        )
                    }
                },
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


async def test_anggaran_bertambah_per_panggilan(db_session: AsyncSession, monkeypatch):
    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 2

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    baris = await db_session.scalar(
        select(PemakaianGemini).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert baris is not None
    assert isinstance(baris.id_pemakaian_gemini, uuid.UUID)
    assert baris.jumlah_panggilan == 2


async def test_anggaran_berhenti_tepat_limit(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 1)
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    await gemini.ocr_grup([], [])
    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 1
    assert sleeps == []

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    jumlah_db = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_db == 1


async def test_anggaran_reset_pergantian_hari(db_session: AsyncSession, monkeypatch):
    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 2

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    besok = hari_ini + timedelta(days=1)

    class _DatetimePalsu:
        @staticmethod
        def now(tz):
            return real_datetime.combine(besok, time(12, 0), tzinfo=tz)

    monkeypatch.setattr(gemini, "datetime", _DatetimePalsu)

    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 1

    # Baris hari baru mulai dari 0 lalu menjadi 1; riwayat hari sebelumnya tetap tersimpan.
    jumlah_hari_ini = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    jumlah_besok = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == besok,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_hari_ini == 2
    assert jumlah_besok == 1


async def test_anggaran_bertahan_setelah_restart(db_session: AsyncSession, monkeypatch):
    """Simulasi restart: objek _Anggaran dibuat ulang (memori kosong), tetapi
    hitungan dan pagar anggaran tetap ditegakkan dari database."""
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 2)
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 1

    # Restart ke-1: memori kosong, panggilan berikutnya melanjutkan dari angka DB (1 -> 2).
    gemini._anggaran = gemini._Anggaran()
    assert gemini._anggaran._hitung == {}

    await gemini.ocr_grup([], [])
    assert gemini._anggaran._hitung[gemini._MODEL] == 2
    assert len(calls) == 2

    # Restart ke-2: memori kembali kosong, tetapi di DB sudah mencapai limit (2)
    # sehingga panggilan langsung ditolak dan memori disinkronkan ke angka DB.
    gemini._anggaran = gemini._Anggaran()
    assert gemini._anggaran._hitung == {}

    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 2
    assert gemini._anggaran._hitung[gemini._MODEL] == 2

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    jumlah_db = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_db == 2


async def test_anggaran_klaim_atomik_dua_panggilan_paralel(db_session: AsyncSession, monkeypatch):
    """Dua panggilan bersamaan (maks 2 paralel) menambah hitungan secara atomik
    tanpa IntegrityError atau lost update, dan tetap menghormati batas kuota."""
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        await asyncio.sleep(0)
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    await asyncio.gather(gemini.ocr_grup([], []), gemini.ocr_grup([], []))
    assert len(calls) == 2

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    baris_list = list(
        await db_session.scalars(
            select(PemakaianGemini).where(
                PemakaianGemini.tanggal == hari_ini,
                PemakaianGemini.model == gemini._MODEL,
            )
        )
    )
    assert len(baris_list) == 1
    assert baris_list[0].jumlah_panggilan == 2

    # Sekarang set limit = 3 (tersisa 1 slot) lalu jalankan 2 panggilan paralel:
    # tepat 1 berhasil dan 1 ditolak KuotaHarianHabis.
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 3)
    hasil_paralel = await asyncio.gather(
        gemini.ocr_grup([], []),
        gemini.ocr_grup([], []),
        return_exceptions=True,
    )
    sukses = [h for h in hasil_paralel if isinstance(h, gemini.ResponsOcr)]
    gagal = [h for h in hasil_paralel if isinstance(h, gemini.KuotaHarianHabis)]
    assert len(sukses) == 1
    assert len(gagal) == 1
    assert len(calls) == 3

    db_session.expire_all()
    jumlah_akhir = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_akhir == 3


async def test_anggaran_retry_ditolak_bila_batas_tercapai(db_session: AsyncSession, monkeypatch):
    """Klaim kuota berlaku per percobaan (termasuk retry): jika percobaan pertama
    menghabiskan slot terakhir lalu gagal sementara (503), percobaan retry ditolak
    dengan KuotaHarianHabis."""
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 1)
    calls: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        calls.append(1)
        raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_grup([], [])
    assert len(calls) == 1
    assert sleeps == [10]

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    jumlah_db = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_db == 1


async def test_anggaran_tidak_hilang_saat_transaksi_pemanggil_rollback(
    db_session: AsyncSession, monkeypatch
):
    """Hitungan dicatat di sesi pendek tersendiri sehingga rollback pada transaksi
    permintaan pemanggil tidak menghapus hitungan panggilan yang sudah dikirim."""

    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)

    db_session.add(
        Pengguna(nama="Sementara", email=f"{uuid.uuid4()}@contoh.com", password_hash="hash")
    )
    await db_session.flush()
    await gemini.ocr_grup([], [])
    await db_session.rollback()

    hari_ini = real_datetime.now(gemini._TZ_LA).date()
    jumlah_db = await db_session.scalar(
        select(PemakaianGemini.jumlah_panggilan).where(
            PemakaianGemini.tanggal == hari_ini,
            PemakaianGemini.model == gemini._MODEL,
        )
    )
    assert jumlah_db == 1


async def test_kegagalan_db_tidak_menggagalkan_ocr_dan_judge_dengan_fallback_memori(
    monkeypatch, caplog
):
    """Kegagalan membaca/menulis hitungan di database tidak boleh menggagalkan
    OCR atau judge: galat dicatat ke log tanpa isi sensitif dan pagar anggaran
    jatuh ke hitungan memori proses."""
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 2)

    class _SesiGagal:
        async def __aenter__(self):
            raise OperationalError(
                'INSERT INTO "Pemakaian_Gemini" VALUES (:rahasia)',
                {"rahasia": "RAHASIA_SENSITIF_DB_ANGGARAN"},
                ConnectionResetError("database down"),
                connection_invalidated=True,
            )

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(gemini, "AsyncSessionLocal", lambda: _SesiGagal())

    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban OCR")])

    async def fake_judge(items):
        return gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=90)])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    monkeypatch.setattr(gemini, "_panggil_sdk_judge", fake_judge)

    with caplog.at_level("ERROR"):
        hasil_ocr = await gemini.ocr_grup([], [1])
        hasil_judge = await gemini.judge_grup(
            [gemini.ItemJudgeMasuk(id_item="0:1", kunci_jawaban="Kunci", teks_jawaban="Jawaban")]
        )
        with pytest.raises(gemini.KuotaHarianHabis):
            await gemini.ocr_grup([], [1])

    assert len(hasil_ocr.items) == 1
    assert hasil_judge.items[0].skor == 90
    assert gemini._anggaran._hitung[gemini._MODEL] == 2
    assert "gemini_anggaran_db_gagal" in caplog.text
    assert "RAHASIA_SENSITIF_DB_ANGGARAN" not in caplog.text


async def test_klaim_anggaran_db_lewat_batas_waktu_jatuh_ke_fallback_memori(monkeypatch, caplog):
    """Bila klaim database melewati _BATAS_WAKTU_DB_ANGGARAN, sesi ditutup bersih
    tanpa bocor, log mencatat gemini_anggaran_db_gagal tanpa isi sensitif, dan
    OCR/judge tetap berjalan memakai fallback memori."""
    monkeypatch.setattr(gemini, "_BATAS_WAKTU_DB_ANGGARAN", 0.02)
    monkeypatch.setattr(settings, "GEMINI_RPD_LIMIT", 2)
    pelacak = {"aktif": 0, "ditutup": 0}

    class _SesiLambat:
        async def __aenter__(self):
            pelacak["aktif"] += 1
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pelacak["aktif"] -= 1
            pelacak["ditutup"] += 1
            return False

        async def scalar(self, stmt):
            await asyncio.sleep(1)
            return 1

        async def commit(self):
            return None

    monkeypatch.setattr(gemini, "AsyncSessionLocal", lambda: _SesiLambat())

    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban OCR")])

    async def fake_judge(items):
        return gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=92)])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    monkeypatch.setattr(gemini, "_panggil_sdk_judge", fake_judge)

    with caplog.at_level("ERROR"):
        hasil_ocr = await gemini.ocr_grup([], [1])
        hasil_judge = await gemini.judge_grup(
            [gemini.ItemJudgeMasuk(id_item="0:1", kunci_jawaban="Kunci", teks_jawaban="Jawaban")]
        )
        with pytest.raises(gemini.KuotaHarianHabis):
            await gemini.ocr_grup([], [1])

    assert len(hasil_ocr.items) == 1
    assert hasil_judge.items[0].skor == 92
    assert gemini._anggaran._hitung[gemini._MODEL] == 2
    assert pelacak["aktif"] == 0
    assert pelacak["ditutup"] == 3
    assert "gemini_anggaran_db_gagal" in caplog.text
    assert "tipe=TimeoutError" in caplog.text


async def test_kegagalan_db_anggaran_tidak_menggagalkan_koreksi_file_jawaban(
    db_session: AsyncSession, tmp_path, monkeypatch, caplog
):
    """Ketika database anggaran gagal, alur koreksi lembar jawaban (OCR + judge +
    simpan Hasil_Koreksi) tetap selesai normal lewat fallback memori."""
    from app.models.batch import Batch
    from app.models.enums import Kategori, StatusProses
    from app.models.file_jawaban import FileJawaban
    from app.models.hasil_koreksi import HasilKoreksi
    from app.models.soal import Soal
    from app.services import pemrosesan

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    pengguna = Pengguna(nama="Budi", email=f"{uuid.uuid4()}@contoh.com", password_hash="hash")
    db_session.add(pengguna)
    await db_session.commit()

    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch="Batch Koreksi")
    db_session.add(batch)
    await db_session.commit()

    soal = Soal(
        id_batch=batch.id_batch, no_soal=1, kunci_jawaban="Fotosintesis menghasilkan glukosa"
    )
    db_session.add(soal)
    await db_session.commit()

    id_file = uuid.uuid4()
    rel_path = f"uploads/{batch.id_batch}/{id_file}.png"
    full_path = tmp_path / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"isi")

    fj = FileJawaban(
        id_file=id_file,
        id_batch=batch.id_batch,
        nama_peserta_didik="Ani",
        path=rel_path,
        status_proses=StatusProses.DIPROSES,
    )
    db_session.add(fj)
    await db_session.commit()

    class _SesiAnggaranGagal:
        async def __aenter__(self):
            raise OperationalError(
                'INSERT INTO "Pemakaian_Gemini"',
                {"kunci": "RAHASIA_KOREKSI"},
                ConnectionResetError("db down"),
                connection_invalidated=True,
            )

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(gemini, "AsyncSessionLocal", lambda: _SesiAnggaranGagal())

    async def fake_ocr(bagian_file, no_soal_list):
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Glukosa dibuat")])

    async def fake_judge(items):
        return gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=85)])

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr", fake_ocr)
    monkeypatch.setattr(gemini, "_panggil_sdk_judge", fake_judge)

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.SELESAI
    assert fj.pesan_error is None

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil is not None
    assert hasil.teks_ocr == "Glukosa dibuat"
    assert hasil.skor_sistem == 85
    assert hasil.kategori == Kategori.SANGAT_MIRIP
    assert gemini._anggaran._hitung[gemini._MODEL] == 2
    assert "gemini_anggaran_db_gagal" in caplog.text
    assert "RAHASIA_KOREKSI" not in caplog.text


async def test_timeout_eksplisit_120_detik():
    client = gemini._ambil_client()
    assert client._api_client._http_options.timeout == gemini._TIMEOUT_MS
    assert gemini._TIMEOUT_MS == 120_000


# --- OCR kunci jawaban (F-KUNCI-FILE): retry lebih ketat, batas waktu total terpisah ---


async def test_prompt_ocr_kunci_memuat_penanda_tidak_ada_teks():
    assert gemini.PENANDA_TIDAK_ADA_TEKS in gemini._prompt_ocr_kunci()


async def test_ocr_kunci_sukses(monkeypatch):
    async def fake_ocr_kunci(konten, ext):
        return "Teks kunci apa adanya"

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)

    hasil = await gemini.ocr_kunci(b"konten", "png")
    assert hasil == "Teks kunci apa adanya"


async def test_ocr_kunci_timeout_per_panggilan_diturunkan():
    konten = b"konten"
    calls = []

    class _ResponsPalsu:
        text = "Teks"

    class _ModelsPalsu:
        async def generate_content(self, model, contents, config):
            calls.append(config.http_options.timeout)
            return _ResponsPalsu()

    class _AioPalsu:
        models = _ModelsPalsu()

    class _ClientPalsu:
        aio = _AioPalsu()

    import app.services.gemini as gemini_module

    gemini_module._client = _ClientPalsu()
    try:
        hasil = await gemini.ocr_kunci(konten, "png")
    finally:
        gemini_module._client = None

    assert hasil == "Teks"
    assert calls == [gemini._TIMEOUT_MS_KUNCI]
    assert gemini._TIMEOUT_MS_KUNCI == 50_000
    # Anggaran waktu: percobaan awal + jeda retry + percobaan ulang <= 120 detik (NFR1).
    assert gemini._TIMEOUT_MS_KUNCI * 2 / 1000 + sum(gemini._RETRY_DELAYS_KUNCI) <= 120


async def test_ocr_kunci_retry_tepat_satu_kali(monkeypatch):
    calls: list[int] = []

    async def fake_ocr_kunci(konten, ext):
        calls.append(1)
        if len(calls) == 1:
            raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})
        return "Teks setelah retry"

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)
    sleeps = _patch_sleep(monkeypatch)

    hasil = await gemini.ocr_kunci(b"konten", "png")
    assert hasil == "Teks setelah retry"
    assert len(calls) == 2
    assert sleeps == [10]


async def test_ocr_kunci_gagal_setelah_satu_retry(monkeypatch):
    calls: list[int] = []

    async def fake_ocr_kunci(konten, ext):
        calls.append(1)
        raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.GagalSementara):
        await gemini.ocr_kunci(b"konten", "png")
    assert len(calls) == 2
    assert sleeps == [10]


async def test_ocr_kunci_tanpa_retry_saat_kuota_harian_habis(monkeypatch):
    calls: list[int] = []

    async def fake_ocr_kunci(konten, ext):
        calls.append(1)
        raise genai_errors.ClientError(429, {"error": {"message": "Resource has been exhausted"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)
    sleeps = _patch_sleep(monkeypatch)

    with pytest.raises(gemini.KuotaHarianHabis):
        await gemini.ocr_kunci(b"konten", "png")
    assert len(calls) == 1
    assert sleeps == []


async def test_ocr_kunci_batas_waktu_total_terjaga_walau_semaphore_penuh(monkeypatch):
    """Batas waktu total (_BATAS_WAKTU_TOTAL_KUNCI) membungkus antrean semaphore:
    jika panggilan tidak pernah mendapat giliran (semaphore penuh selamanya),
    hasilnya tetap GagalSementara, bukan menggantung tanpa batas."""
    monkeypatch.setattr(gemini, "_BATAS_WAKTU_TOTAL_KUNCI", 0.05)

    async def fake_ocr_kunci(konten, ext):
        return "tidak akan tercapai"

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)

    async with gemini._SEM, gemini._SEM:
        with pytest.raises(gemini.GagalSementara):
            await gemini.ocr_kunci(b"konten", "png")


async def test_ocr_kunci_timeout_total_saat_menunggu_retry_jadi_gagal_sementara(monkeypatch):
    """Batas waktu total (_BATAS_WAKTU_TOTAL_KUNCI) juga membungkus jeda retry
    (asyncio.sleep asli, tanpa mock): jika timeout habis saat menunggu retry,
    hasilnya GagalSementara (bukan CancelledError)."""
    monkeypatch.setattr(gemini, "_BATAS_WAKTU_TOTAL_KUNCI", 0.05)
    calls: list[int] = []

    async def fake_ocr_kunci(konten, ext):
        calls.append(1)
        raise genai_errors.ServerError(503, {"error": {"message": "unavailable"}})

    monkeypatch.setattr(gemini, "_panggil_sdk_ocr_kunci", fake_ocr_kunci)

    with pytest.raises(gemini.GagalSementara):
        await gemini.ocr_kunci(b"konten", "png")
    assert len(calls) == 1


# --- Judge: system_instruction, parameter default, dan format input JSON ---


async def test_judge_config_memuat_system_instruction_tanpa_parameter_sampling():
    konfigs: list = []

    class _ResponsPalsu:
        text = '{"items": []}'

    class _ModelsPalsu:
        async def generate_content(self, model, contents, config):
            konfigs.append(config)
            return _ResponsPalsu()

    class _AioPalsu:
        models = _ModelsPalsu()

    class _ClientPalsu:
        aio = _AioPalsu()

    import app.services.gemini as gemini_module

    gemini_module._client = _ClientPalsu()
    try:
        await gemini._panggil_sdk_judge(
            [gemini.ItemJudgeMasuk(id_item="0:1", kunci_jawaban="kunci", teks_jawaban="jawaban")]
        )
    finally:
        gemini_module._client = None

    assert len(konfigs) == 1
    config = konfigs[0]
    assert config.system_instruction is not None
    assert "sendiri-sendiri" in config.system_instruction
    assert "sebagian" in config.system_instruction
    assert "kesetaraan klaim" in config.system_instruction
    assert config.temperature is None
    assert config.top_p is None
    assert config.top_k is None
    assert config.thinking_config is None
    assert config.seed is None


async def test_judge_input_json_tidak_ambigu_untuk_teks_bergaris_baru():
    import json as json_module

    konten_terkirim: list = []

    class _ResponsPalsu:
        text = '{"items": []}'

    class _ModelsPalsu:
        async def generate_content(self, model, contents, config):
            konten_terkirim.append(contents)
            return _ResponsPalsu()

    class _AioPalsu:
        models = _ModelsPalsu()

    class _ClientPalsu:
        aio = _AioPalsu()

    import app.services.gemini as gemini_module

    teks_jawaban_asli = "Baris pertama jawaban.\nBaris kedua dengan lanjutan.\nBaris ketiga."
    kunci_asli = "Kunci\njuga\nbisa\nmultibaris."

    gemini_module._client = _ClientPalsu()
    try:
        await gemini._panggil_sdk_judge(
            [
                gemini.ItemJudgeMasuk(
                    id_item="0:1", kunci_jawaban=kunci_asli, teks_jawaban=teks_jawaban_asli
                )
            ]
        )
    finally:
        gemini_module._client = None

    assert len(konten_terkirim) == 1
    (daftar_item_terkirim,) = konten_terkirim[0]
    items_terparse = json_module.loads(daftar_item_terkirim)
    assert len(items_terparse) == 1
    assert items_terparse[0]["id_item"] == "0:1"
    assert items_terparse[0]["kunci_jawaban"] == kunci_asli
    assert items_terparse[0]["teks_jawaban"] == teks_jawaban_asli
