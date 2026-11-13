import asyncio
import shutil
import threading
import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
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
    return pemrosesan._Berkas(row=None, konten=b"0" * ukuran_byte, ext="png", halaman=halaman)


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
