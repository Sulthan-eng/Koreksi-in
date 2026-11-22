import asyncio
import shutil
import threading
import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.batch import Batch
from app.models.enums import Kategori, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import gemini, pemrosesan


@pytest.fixture(autouse=True)
def _upload_dir_sementara(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


async def _buat_pengguna(db: AsyncSession) -> Pengguna:
    pengguna = Pengguna(nama="Budi", email=f"{uuid.uuid4()}@contoh.com", password_hash="hash")
    db.add(pengguna)
    await db.commit()
    return pengguna


async def _buat_batch(db: AsyncSession, no_soal_list: list[int]) -> tuple[Batch, list[Soal]]:
    pengguna = await _buat_pengguna(db)
    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch="Batch")
    db.add(batch)
    await db.commit()
    soal_list = [
        Soal(id_batch=batch.id_batch, no_soal=no_soal, kunci_jawaban="Kunci")
        for no_soal in no_soal_list
    ]
    db.add_all(soal_list)
    await db.commit()
    return batch, soal_list


def _tulis_file(tmp_path: Path, id_batch: uuid.UUID, id_file: uuid.UUID, ext: str) -> str:
    rel = f"uploads/{id_batch}/{id_file}.{ext}"
    full = tmp_path / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(b"\x89PNG\r\n\x1a\n" + b"isi")
    return rel


async def _buat_file_jawaban(db: AsyncSession, tmp_path: Path, batch: Batch) -> FileJawaban:
    id_file = uuid.uuid4()
    rel = _tulis_file(tmp_path, batch.id_batch, id_file, "png")
    fj = FileJawaban(
        id_file=id_file,
        id_batch=batch.id_batch,
        nama_peserta_didik="Budi",
        path=rel,
        status_proses=StatusProses.DIPROSES,
    )
    db.add(fj)
    await db.commit()
    return fj


def _fake_berkas(ukuran_byte: int, halaman: int = 1) -> pemrosesan._Berkas:
    return pemrosesan._Berkas(
        id_file=uuid.uuid4(), konten=b"0" * ukuran_byte, ext="png", halaman=halaman
    )


def _url_test():
    base = make_url(settings.DATABASE_URL)
    return base.set(database=f"{base.database}_test", drivername="postgresql+asyncpg")


async def _hapus_batch_async(id_batch: uuid.UUID) -> None:
    """Simulasikan DELETE /api/batch/{id} dari request lain: sesi dan koneksi
    terpisah dari db_session yang dipakai pemrosesan di test."""
    engine = create_async_engine(_url_test(), poolclass=NullPool)
    try:
        async with AsyncSession(engine) as sesi:
            batch = await sesi.get(Batch, id_batch)
            if batch is not None:
                await sesi.delete(batch)
                await sesi.commit()
    finally:
        await engine.dispose()


def _hapus_batch_lewat_sesi_lain(id_batch: uuid.UUID) -> None:
    """Jalankan penghapusan di event loop terpisah (thread lain) agar benar-benar
    independen dari loop yang sedang menjalankan tugas pemrosesan, meniru request
    DELETE yang datang bersamaan saat tugas latar berjalan."""

    def _jalankan() -> None:
        asyncio.run(_hapus_batch_async(id_batch))

    t = threading.Thread(target=_jalankan)
    t.start()
    t.join()


def test_kategori_dari_skor_batas() -> None:
    assert pemrosesan.kategori_dari_skor(39) == Kategori.KURANG_MIRIP
    assert pemrosesan.kategori_dari_skor(40) == Kategori.CUKUP_MIRIP
    assert pemrosesan.kategori_dari_skor(79) == Kategori.CUKUP_MIRIP
    assert pemrosesan.kategori_dari_skor(80) == Kategori.SANGAT_MIRIP


def test_buat_grup_file_tunggal_besar_tetap_satu_grup() -> None:
    besar = _fake_berkas(10 * 1024 * 1024, halaman=15)
    assert pemrosesan._buat_grup([besar]) == [[besar]]


def test_buat_grup_pecah_pada_batas_jumlah_file() -> None:
    daftar = [_fake_berkas(1024) for _ in range(6)]
    grup = pemrosesan._buat_grup(daftar)
    assert [len(g) for g in grup] == [5, 1]


def test_buat_grup_pecah_pada_batas_halaman() -> None:
    daftar = [_fake_berkas(1024, halaman=8), _fake_berkas(1024, halaman=8)]
    grup = pemrosesan._buat_grup(daftar)
    assert [len(g) for g in grup] == [1, 1]


def test_buat_grup_tepat_10mb_tetap_satu_grup() -> None:
    besar = _fake_berkas(10 * 1024 * 1024)
    assert pemrosesan._buat_grup([besar]) == [[besar]]


def test_buat_grup_dua_file_6mb_jadi_dua_grup() -> None:
    daftar = [_fake_berkas(6 * 1024 * 1024), _fake_berkas(6 * 1024 * 1024)]
    grup = pemrosesan._buat_grup(daftar)
    assert [len(g) for g in grup] == [1, 1]


async def test_jawaban_kosong_tidak_memicu_judge(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(gemini, "ocr_grup", AsyncMock(return_value=gemini.ResponsOcr(items=[])))
    judge_mock = AsyncMock()
    monkeypatch.setattr(gemini, "judge_grup", judge_mock)

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    judge_mock.assert_not_called()
    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil.teks_ocr == ""
    assert hasil.skor_sistem == 0
    assert hasil.kategori == Kategori.KURANG_MIRIP
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.SELESAI


async def test_idempotent_tidak_duplikat(db_session: AsyncSession, tmp_path, monkeypatch) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=90)])
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)
    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil = list(
        await db_session.scalars(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    )
    assert len(hasil) == 1
    assert hasil[0].skor_sistem == 90


async def test_muat_berkas_gagal_tandai_semua_file_gagal(
    db_session: AsyncSession, tmp_path
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj1 = await _buat_file_jawaban(db_session, tmp_path, batch)
    fj2 = await _buat_file_jawaban(db_session, tmp_path, batch)

    (tmp_path / fj1.path).unlink()

    await pemrosesan.proses_file_jawaban([fj1.id_file, fj2.id_file], db=db_session)

    await db_session.refresh(fj1)
    await db_session.refresh(fj2)
    assert fj1.status_proses == StatusProses.GAGAL
    assert fj1.pesan_error == pemrosesan.PESAN_GAGAL_UMUM
    assert fj2.status_proses == StatusProses.GAGAL
    assert fj2.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_grup_gagal_tidak_pengaruhi_grup_lain(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]

    panggilan = {"n": 0}

    async def fake_ocr(bagian_file, no_soal_list):
        panggilan["n"] += 1
        if panggilan["n"] == 2:
            raise gemini.GagalPermanen()
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr)

    await pemrosesan.proses_file_jawaban([f.id_file for f in files], db=db_session)

    for f in files[:5]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.SELESAI
    for f in files[5:]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.GAGAL
        assert f.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_ocr_sukses_judge_gagal_simpan_teks_ocr(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban asli")]
            )
        ),
    )

    async def fake_judge(items):
        raise gemini.GagalPermanen()

    monkeypatch.setattr(gemini, "judge_grup", fake_judge)

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil.teks_ocr == "Jawaban asli"
    assert hasil.skor_sistem is None
    assert hasil.kategori is None
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.GAGAL
    assert fj.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_pesan_error_kuota_vs_umum(db_session: AsyncSession, tmp_path, monkeypatch) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj1 = await _buat_file_jawaban(db_session, tmp_path, batch)

    async def fake_ocr_kuota(bagian_file, no_soal_list):
        raise gemini.KuotaHarianHabis()

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr_kuota)
    await pemrosesan.proses_file_jawaban([fj1.id_file], db=db_session)
    await db_session.refresh(fj1)
    assert fj1.pesan_error == pemrosesan.PESAN_SIBUK_KUOTA

    fj2 = await _buat_file_jawaban(db_session, tmp_path, batch)

    async def fake_ocr_permanen(bagian_file, no_soal_list):
        raise gemini.GagalPermanen()

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr_permanen)
    await pemrosesan.proses_file_jawaban([fj2.id_file], db=db_session)
    await db_session.refresh(fj2)
    assert fj2.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_exception_tak_terduga_tidak_hentikan_grup_lain(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]

    panggilan = {"n": 0}

    async def fake_ocr(bagian_file, no_soal_list):
        panggilan["n"] += 1
        if panggilan["n"] == 2:
            raise RuntimeError("bug tak terduga")
        return gemini.ResponsOcr(items=[])

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr)

    await pemrosesan.proses_file_jawaban([f.id_file for f in files], db=db_session)

    for f in files[:5]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.SELESAI
    for f in files[5:]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.GAGAL
        assert f.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_commit_per_grup(db_session: AsyncSession, tmp_path, monkeypatch) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]

    monkeypatch.setattr(gemini, "ocr_grup", AsyncMock(return_value=gemini.ResponsOcr(items=[])))

    komit = {"n": 0}
    asli_commit = db_session.commit

    async def hitung_commit():
        komit["n"] += 1
        await asli_commit()

    monkeypatch.setattr(db_session, "commit", hitung_commit)

    await pemrosesan.proses_file_jawaban([f.id_file for f in files], db=db_session)

    assert komit["n"] == 2


async def test_skor_di_luar_rentang_jadi_null(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=150)])
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil.skor_sistem is None
    assert hasil.kategori is None
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.GAGAL


async def test_id_item_tidak_dikenal_diabaikan(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(
                items=[
                    gemini.HasilJudgeItem(id_item="0:1", skor=90),
                    gemini.HasilJudgeItem(id_item="9:9", skor=50),
                ]
            )
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil.skor_sistem == 90
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.SELESAI


async def test_item_tidak_kembali_dari_judge_jadi_null(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, soal_list = await _buat_batch(db_session, [1, 2])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[
                    gemini.HasilOcrItem(id_item="0:1", teks="Jawaban satu"),
                    gemini.HasilOcrItem(id_item="0:2", teks="Jawaban dua"),
                ]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=70)])
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil_satu = await db_session.scalar(
        select(HasilKoreksi).where(HasilKoreksi.id_soal == soal_list[0].id_soal)
    )
    hasil_dua = await db_session.scalar(
        select(HasilKoreksi).where(HasilKoreksi.id_soal == soal_list[1].id_soal)
    )
    assert hasil_satu.skor_sistem == 70
    assert hasil_dua.skor_sistem is None
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.GAGAL


async def test_ocr_no_soal_ganda_ambil_satu(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[
                    gemini.HasilOcrItem(id_item="0:1", teks="Jawaban pertama"),
                    gemini.HasilOcrItem(id_item="0:1", teks="Jawaban kedua"),
                ]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=85)])
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    assert hasil.teks_ocr == "Jawaban pertama"


async def test_ocr_no_soal_di_luar_batch_diabaikan(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[
                    gemini.HasilOcrItem(id_item="0:1", teks="Jawaban satu"),
                    gemini.HasilOcrItem(id_item="0:99", teks="Nomor di luar batch"),
                ]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=85)])
        ),
    )

    await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    daftar_hasil = list(
        await db_session.scalars(select(HasilKoreksi).where(HasilKoreksi.id_file == fj.id_file))
    )
    assert len(daftar_hasil) == 1
    assert daftar_hasil[0].teks_ocr == "Jawaban satu"


async def test_batch_terhapus_saat_ocr_berjalan_tidak_error_dan_tanpa_hasil_yatim(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    """Pembuktian untuk FR22: batch dihapus (lewat sesi/koneksi lain) persis saat
    tugas latar sedang menunggu Gemini. Tugas latar TIDAK BOLEH error dan TIDAK
    BOLEH menulis Hasil_Koreksi untuk batch yang sudah hilang."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)
    id_batch, id_file = batch.id_batch, fj.id_file

    async def fake_ocr(bagian_file, no_soal_list):
        _hapus_batch_lewat_sesi_lain(id_batch)
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")])

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr)
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=90)])
        ),
    )

    await pemrosesan.proses_file_jawaban([id_file], db=db_session)

    hasil = await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == id_file))
    assert hasil is None
    assert await db_session.get(Batch, id_batch) is None


async def test_baris_dan_berkas_hilang_sebelum_dimuat_tidak_error(
    db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    """Pembuktian untuk FR22: baris File_Jawaban dan berkas fisiknya sudah
    terhapus (batch dihapus lewat sesi lain) tepat sebelum _muat_berkas membaca.
    Tugas latar TIDAK BOLEH melempar exception ke pemanggil."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj1 = await _buat_file_jawaban(db_session, tmp_path, batch)
    fj2 = await _buat_file_jawaban(db_session, tmp_path, batch)

    asli_muat_berkas = pemrosesan._muat_berkas
    sudah_dihapus = {"v": False}

    async def fake_muat_berkas(row):
        if not sudah_dihapus["v"]:
            sudah_dihapus["v"] = True
            _hapus_batch_lewat_sesi_lain(batch.id_batch)
            shutil.rmtree(tmp_path / "uploads" / str(batch.id_batch), ignore_errors=True)
        return await asli_muat_berkas(row)

    monkeypatch.setattr(pemrosesan, "_muat_berkas", fake_muat_berkas)

    await pemrosesan.proses_file_jawaban([fj1.id_file, fj2.id_file], db=db_session)

    assert await db_session.scalar(select(HasilKoreksi)) is None


def _pasang_session_factory_pelacak(monkeypatch, engine, on_sesi=None) -> dict:
    """Patch pemrosesan.AsyncSessionLocal memakai _engine DB uji agar jalur
    produksi (db=None) dapat diuji tanpa pernah menyentuh DB pengembangan."""
    base_factory = async_sessionmaker(engine, expire_on_commit=False)
    pelacak = {"aktif": 0, "total": 0, "sesi_ids": []}

    class _KonteksSesiPelacak:
        def __init__(self) -> None:
            self._cm = base_factory()
            self._sesi: AsyncSession | None = None

        async def __aenter__(self) -> AsyncSession:
            pelacak["total"] += 1
            urutan = pelacak["total"]
            self._sesi = await self._cm.__aenter__()
            pelacak["aktif"] += 1
            pelacak["sesi_ids"].append(id(self._sesi))
            if on_sesi is not None:
                on_sesi(urutan, self._sesi)
            return self._sesi

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            try:
                return await self._cm.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                pelacak["aktif"] -= 1

    monkeypatch.setattr(pemrosesan, "AsyncSessionLocal", _KonteksSesiPelacak)
    return pelacak


async def test_sesi_pendek_tidak_ada_sesi_aktif_selama_muat_berkas_dan_gemini(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    """Jalur produksi (db=None): sesi baca ditutup sebelum muat berkas dan
    panggilan Gemini; setiap grup membuka dan menutup sesi simpan sendiri."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]
    id_files = [f.id_file for f in files]

    pelacak = _pasang_session_factory_pelacak(monkeypatch, _engine)
    aktif_saat_muat: list[int] = []
    aktif_saat_ocr: list[int] = []
    aktif_saat_judge: list[int] = []

    asli_muat = pemrosesan._muat_berkas

    async def pantau_muat(data_file):
        aktif_saat_muat.append(pelacak["aktif"])
        return await asli_muat(data_file)

    async def fake_ocr(bagian_file, no_soal_list):
        aktif_saat_ocr.append(pelacak["aktif"])
        return gemini.ResponsOcr(
            items=[
                gemini.HasilOcrItem(id_item=f"{i}:1", teks=f"Jawaban {i}")
                for i in range(len(bagian_file))
            ]
        )

    async def fake_judge(items):
        aktif_saat_judge.append(pelacak["aktif"])
        return gemini.ResponsJudge(
            items=[gemini.HasilJudgeItem(id_item=it.id_item, skor=85) for it in items]
        )

    monkeypatch.setattr(pemrosesan, "_muat_berkas", pantau_muat)
    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr)
    monkeypatch.setattr(gemini, "judge_grup", fake_judge)

    await pemrosesan.proses_file_jawaban(id_files)

    assert aktif_saat_muat == [0, 0, 0, 0, 0, 0]
    assert aktif_saat_ocr == [0, 0]
    assert aktif_saat_judge == [0, 0]
    assert pelacak["aktif"] == 0
    # 1 sesi baca awal + 2 sesi simpan (grup 1: 5 file, grup 2: 1 file).
    assert pelacak["total"] == 3
    assert len(set(pelacak["sesi_ids"])) == 3

    for f in files:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.SELESAI
        assert f.pesan_error is None
    hasil = list(
        await db_session.scalars(select(HasilKoreksi).where(HasilKoreksi.id_file.in_(id_files)))
    )
    assert len(hasil) == 6
    assert all(h.skor_sistem == 85 and h.kategori == Kategori.SANGAT_MIRIP for h in hasil)


async def test_sesi_pendek_saat_ocr_gagal_dan_judge_gagal(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj_ocr = await _buat_file_jawaban(db_session, tmp_path, batch)
    fj_judge = await _buat_file_jawaban(db_session, tmp_path, batch)

    pelacak = _pasang_session_factory_pelacak(monkeypatch, _engine)
    aktif_saat_ocr: list[int] = []

    async def fake_ocr_sibuk(bagian_file, no_soal_list):
        aktif_saat_ocr.append(pelacak["aktif"])
        raise gemini.GagalSementara()

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr_sibuk)
    await pemrosesan.proses_file_jawaban([fj_ocr.id_file])

    assert aktif_saat_ocr == [0]
    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 2
    await db_session.refresh(fj_ocr)
    assert fj_ocr.status_proses == StatusProses.GAGAL
    assert fj_ocr.pesan_error == pemrosesan.PESAN_SIBUK_KUOTA

    aktif_saat_judge: list[int] = []

    async def fake_ocr_ok(bagian_file, no_soal_list):
        aktif_saat_ocr.append(pelacak["aktif"])
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Teks OCR")])

    async def fake_judge_gagal(items):
        aktif_saat_judge.append(pelacak["aktif"])
        raise gemini.GagalPermanen()

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr_ok)
    monkeypatch.setattr(gemini, "judge_grup", fake_judge_gagal)
    await pemrosesan.proses_file_jawaban([fj_judge.id_file])

    assert aktif_saat_ocr == [0, 0]
    assert aktif_saat_judge == [0]
    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 4
    await db_session.refresh(fj_judge)
    assert fj_judge.status_proses == StatusProses.GAGAL
    assert fj_judge.pesan_error == pemrosesan.PESAN_GAGAL_UMUM
    hasil_judge = await db_session.scalar(
        select(HasilKoreksi).where(HasilKoreksi.id_file == fj_judge.id_file)
    )
    assert hasil_judge.teks_ocr == "Teks OCR"
    assert hasil_judge.skor_sistem is None


async def test_sesi_pendek_batch_terhapus_saat_ocr_berjalan_tanpa_error(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch
) -> None:
    """Skenario FR22 pada jalur produksi (db=None): tidak ada DetachedInstanceError
    atau Hasil_Koreksi yatim saat batch dihapus di tengah fase Gemini."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)
    id_batch, id_file = batch.id_batch, fj.id_file

    pelacak = _pasang_session_factory_pelacak(monkeypatch, _engine)
    aktif_saat_ocr: list[int] = []

    async def fake_ocr(bagian_file, no_soal_list):
        aktif_saat_ocr.append(pelacak["aktif"])
        _hapus_batch_lewat_sesi_lain(id_batch)
        return gemini.ResponsOcr(items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")])

    monkeypatch.setattr(gemini, "ocr_grup", fake_ocr)
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=90)])
        ),
    )

    await pemrosesan.proses_file_jawaban([id_file])

    assert aktif_saat_ocr == [0]
    assert pelacak["aktif"] == 0
    assert (
        await db_session.scalar(select(HasilKoreksi).where(HasilKoreksi.id_file == id_file)) is None
    )


async def test_sesi_pendek_error_db_grup_satu_tidak_hentikan_grup_dua(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch, caplog
) -> None:
    """Bila sesi simpan grup 1 gagal karena DBAPIError, sesi baru menandai grup 1
    gagal (tanpa membocorkan parameter SQL ke log) dan grup 2 tetap selesai."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]

    def gagalkan_simpan_grup_satu(urutan: int, sesi: AsyncSession) -> None:
        # Urutan sesi: 1 = baca awal, 2 = simpan grup 1, 3 = tandai gagal grup 1, 4 = simpan grup 2.
        if urutan == 2:

            async def commit_gagal():
                raise OperationalError(
                    'INSERT INTO "Hasil_Koreksi" VALUES (:teks)',
                    {"teks": "RAHASIA_TEKS_JAWABAN_GRUP1"},
                    ConnectionResetError("connection lost"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "commit", commit_gagal)

    pelacak = _pasang_session_factory_pelacak(
        monkeypatch, _engine, on_sesi=gagalkan_simpan_grup_satu
    )
    monkeypatch.setattr(gemini, "ocr_grup", AsyncMock(return_value=gemini.ResponsOcr(items=[])))

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([f.id_file for f in files])

    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 4
    assert "pemrosesan_grup_gagal_db" in caplog.text
    assert "RAHASIA_TEKS_JAWABAN_GRUP1" not in caplog.text

    for f in files[:5]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.GAGAL
        assert f.pesan_error == pemrosesan.PESAN_GAGAL_UMUM
    await db_session.refresh(files[5])
    assert files[5].status_proses == StatusProses.SELESAI


async def test_tandai_gagal_juga_gagal_tidak_melempar_dan_lanjut_grup_berikutnya(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch, caplog
) -> None:
    """Bila penandaan gagal untuk grup 1 juga gagal karena DB tidak terjangkau,
    _tandai_id_gagal_aman tidak boleh melempar, mencatat logger.error tanpa
    parameter SQL, dan tetap melanjutkan pemrosesan ke grup 2."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    files = [await _buat_file_jawaban(db_session, tmp_path, batch) for _ in range(6)]

    def gagalkan_simpan_dan_tandai_grup_satu(urutan: int, sesi: AsyncSession) -> None:
        # Urutan sesi: 1 = baca awal, 2 = simpan grup 1 (gagal),
        # 3 = tandai gagal grup 1 (juga gagal), 4 = simpan grup 2 (berhasil).
        if urutan in (2, 3):

            async def commit_gagal():
                raise OperationalError(
                    'UPDATE "File_Jawaban" SET pesan_error = :pesan',
                    {"pesan": "RAHASIA_PARAM_TANDAI_GAGAL"},
                    ConnectionResetError("db unreachable"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "commit", commit_gagal)

    pelacak = _pasang_session_factory_pelacak(
        monkeypatch, _engine, on_sesi=gagalkan_simpan_dan_tandai_grup_satu
    )
    monkeypatch.setattr(gemini, "ocr_grup", AsyncMock(return_value=gemini.ResponsOcr(items=[])))

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([f.id_file for f in files])

    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 4
    assert "pemrosesan_tandai_gagal_error" in caplog.text
    assert "RAHASIA_PARAM_TANDAI_GAGAL" not in caplog.text

    # Grup 1 tertinggal 'diproses' (akan disapu sapu_proses_tergantung saat startup),
    # sementara grup 2 tetap berjalan dan selesai normal.
    for f in files[:5]:
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.DIPROSES
    await db_session.refresh(files[5])
    assert files[5].status_proses == StatusProses.SELESAI


async def test_baca_awal_gagal_dbapi_tandai_gagal_tanpa_bocor_param(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch, caplog
) -> None:
    """Bila fase 1 (_baca_data_awal) gagal karena DBAPIError, semua baris
    ditandai gagal lewat helper aman tanpa membocorkan parameter SQL ke log,
    dan storage/Gemini tidak dipanggil."""
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj1 = await _buat_file_jawaban(db_session, tmp_path, batch)
    fj2 = await _buat_file_jawaban(db_session, tmp_path, batch)

    def gagalkan_baca_awal(urutan: int, sesi: AsyncSession) -> None:
        # Urutan sesi: 1 = baca awal (gagal), 2 = tandai gagal aman (berhasil).
        if urutan == 1:

            async def scalars_gagal(*args, **kwargs):
                raise OperationalError(
                    'SELECT * FROM "File_Jawaban" WHERE id_file = :id',
                    {"id": "RAHASIA_PARAM_FASE1"},
                    ConnectionResetError("connection lost"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "scalars", scalars_gagal)

    pelacak = _pasang_session_factory_pelacak(monkeypatch, _engine, on_sesi=gagalkan_baca_awal)
    muat_mock = AsyncMock()
    ocr_mock = AsyncMock()
    monkeypatch.setattr(pemrosesan, "_muat_berkas", muat_mock)
    monkeypatch.setattr(gemini, "ocr_grup", ocr_mock)

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([fj1.id_file, fj2.id_file])

    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 2
    muat_mock.assert_not_called()
    ocr_mock.assert_not_called()
    assert "pemrosesan_baca_awal_gagal_db" in caplog.text
    assert "RAHASIA_PARAM_FASE1" not in caplog.text

    for f in (fj1, fj2):
        await db_session.refresh(f)
        assert f.status_proses == StatusProses.GAGAL
        assert f.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_baca_awal_gagal_tak_terduga_tandai_gagal(
    db_session: AsyncSession, tmp_path, monkeypatch, caplog
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    async def baca_meledak(id_file_list, db):
        raise RuntimeError("galat fase 1 tak terduga")

    monkeypatch.setattr(pemrosesan, "_baca_data_awal", baca_meledak)

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([fj.id_file], db=db_session)

    assert "pemrosesan_baca_awal_gagal_tak_terduga" in caplog.text
    await db_session.refresh(fj)
    assert fj.status_proses == StatusProses.GAGAL
    assert fj.pesan_error == pemrosesan.PESAN_GAGAL_UMUM


async def test_baca_awal_gagal_dan_tandai_gagal_juga_gagal_tidak_melempar(
    _engine, db_session: AsyncSession, tmp_path, monkeypatch, caplog
) -> None:
    batch, _soal_list = await _buat_batch(db_session, [1])
    fj = await _buat_file_jawaban(db_session, tmp_path, batch)

    def gagalkan_semua_sesi(urutan: int, sesi: AsyncSession) -> None:
        if urutan == 1:

            async def scalars_gagal(*args, **kwargs):
                raise OperationalError(
                    'SELECT * FROM "File_Jawaban"',
                    {"rahasia": "RAHASIA_FASE1_MATI"},
                    ConnectionResetError("db unreachable"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "scalars", scalars_gagal)
        elif urutan == 2:

            async def execute_gagal(*args, **kwargs):
                raise OperationalError(
                    'UPDATE "File_Jawaban" SET pesan_error = :pesan',
                    {"pesan": "RAHASIA_TANDAI_MATI"},
                    ConnectionResetError("db unreachable"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "execute", execute_gagal)

    pelacak = _pasang_session_factory_pelacak(monkeypatch, _engine, on_sesi=gagalkan_semua_sesi)

    with caplog.at_level("ERROR"):
        await pemrosesan.proses_file_jawaban([fj.id_file])

    assert pelacak["aktif"] == 0
    assert pelacak["total"] == 2
    assert "pemrosesan_baca_awal_gagal_db" in caplog.text
    assert "pemrosesan_tandai_gagal_error" in caplog.text
    assert "RAHASIA_FASE1_MATI" not in caplog.text
    assert "RAHASIA_TANDAI_MATI" not in caplog.text


async def test_baca_awal_gagal_lalu_coba_lagi_sukses_sampai_selesai(
    client,
    _engine,
    db_session: AsyncSession,
    tmp_path,
    monkeypatch,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    """Alur ujung ke ujung: fase 1 gagal menandai file 'gagal', sehingga pengguna
    langsung dapat menekan 'Coba Lagi' dan pemrosesan berikutnya berakhir 'selesai'."""
    await client.post(
        "/api/auth/daftar",
        json={"nama": "Budi", "email": "budi-fase1@contoh.com", "password": "rahasia123"},
    )
    masuk = await client.post(
        "/api/auth/masuk",
        json={"email": "budi-fase1@contoh.com", "password": "rahasia123"},
    )
    headers = {"Authorization": f"Bearer {masuk.json()['access_token']}"}

    id_batch = (
        await client.post("/api/batch", json={"nama_batch": "UTS Fase 1"}, headers=headers)
    ).json()["id_batch"]
    await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Kunci jawaban"}, headers=headers
    )

    unggah = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=[("files", ("lembar.png", b"\x89PNG\r\n\x1a\n" + b"isi", "image/png"))],
        data={"nama_peserta_didik": "Ani"},
        headers=headers,
    )
    assert unggah.status_code == 201
    id_file = unggah.json()[0]["id_file"]

    # Jalankan tugas latar unggahan dengan fase 1 gagal (DBAPIError) pada sesi 1.
    def gagalkan_baca_awal(urutan: int, sesi: AsyncSession) -> None:
        if urutan == 1:

            async def scalars_gagal(*args, **kwargs):
                raise OperationalError(
                    'SELECT * FROM "File_Jawaban"',
                    {},
                    ConnectionResetError("pooler reset"),
                    connection_invalidated=True,
                )

            monkeypatch.setattr(sesi, "scalars", scalars_gagal)

    _pasang_session_factory_pelacak(monkeypatch, _engine, on_sesi=gagalkan_baca_awal)
    func, args, kwargs = _background_tasks_tidak_dijalankan[-1]
    assert func is pemrosesan.proses_file_jawaban
    await func(*args, **kwargs)
    # Fixture client memakai satu db_session bersama, sementara tugas latar commit di sesi terpisah.
    db_session.expire_all()

    daftar = (await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=headers)).json()
    assert daftar[0]["status_proses"] == "gagal"
    assert daftar[0]["pesan_error"] == pemrosesan.PESAN_GAGAL_UMUM

    # Pengguna menekan "Coba Lagi".
    coba_lagi = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{id_file}/coba-lagi", headers=headers
    )
    assert coba_lagi.status_code == 200
    assert coba_lagi.json()["status_proses"] == "diproses"
    assert coba_lagi.json()["pesan_error"] is None

    baris = await db_session.get(FileJawaban, uuid.UUID(id_file), populate_existing=True)
    assert baris.jumlah_retry == 1

    # Pemrosesan ulang berjalan normal sampai selesai.
    _pasang_session_factory_pelacak(monkeypatch, _engine)
    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban Ani")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=88)])
        ),
    )
    func_ulang, args_ulang, kwargs_ulang = _background_tasks_tidak_dijalankan[-1]
    assert func_ulang is pemrosesan.proses_file_jawaban
    await func_ulang(*args_ulang, **kwargs_ulang)
    db_session.expire_all()

    daftar_akhir = (await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=headers)).json()
    assert daftar_akhir[0]["status_proses"] == "selesai"
    assert daftar_akhir[0]["pesan_error"] is None

    hasil = (await client.get(f"/api/batch/{id_batch}/hasil", headers=headers)).json()
    assert len(hasil) == 1
    assert hasil[0]["skor_sistem"] == 88
    assert hasil[0]["kategori"] == "sangat_mirip"
