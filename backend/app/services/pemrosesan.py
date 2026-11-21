"""Pengelompokan file, pipeline OCR lalu judge per grup, dan penyimpanan
Hasil_Koreksi (SPEC bagian 8). Dipanggil lewat BackgroundTasks setelah unggah.

Pipeline memakai sesi database pendek per fase agar koneksi pool tidak pernah
ditahan selama pembacaan berkas (storage) atau panggilan Gemini:
1. Sesi baca pendek: muat metadata File_Jawaban & Soal, salin ke dataclass
   polos, lalu tutup sesi.
2. Fase storage & Gemini: muat berkas, kelompokkan, lalu jalankan OCR dan judge
   per grup tanpa sesi DB terbuka.
3. Sesi simpan baru per grup: cek baris masih ada (FR22), upsert Hasil_Koreksi,
   perbarui status File_Jawaban, commit, lalu tutup sesi.
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.enums import Kategori, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.soal import Soal
from app.services import gemini
from app.storage import dapatkan_storage
from app.utils.berkas import hitung_halaman

logger = logging.getLogger(__name__)

_MAKS_FILE_PER_GRUP = 5
_MAKS_UKURAN_GRUP_BYTE = 10 * 1024 * 1024
_MAKS_HALAMAN_GRUP = 15

PESAN_SIBUK_KUOTA = "Layanan AI sedang sibuk atau kuota harian habis, coba lagi nanti."
PESAN_GAGAL_UMUM = "Gagal membaca file, silakan coba lagi."


def kategori_dari_skor(skor: int) -> Kategori:
    if skor >= 80:
        return Kategori.SANGAT_MIRIP
    if skor >= 40:
        return Kategori.CUKUP_MIRIP
    return Kategori.KURANG_MIRIP


@dataclass(frozen=True)
class _DataFile:
    id_file: uuid.UUID
    id_batch: uuid.UUID
    path: str


@dataclass(frozen=True)
class _DataSoal:
    id_soal: uuid.UUID
    no_soal: int
    kunci_jawaban: str


@dataclass(frozen=True)
class _Berkas:
    id_file: uuid.UUID
    konten: bytes
    ext: str
    halaman: int

    @property
    def ukuran(self) -> int:
        return len(self.konten)


@dataclass(frozen=True)
class _BarisHasil:
    id_file: uuid.UUID
    id_soal: uuid.UUID
    teks_ocr: str
    skor_sistem: int | None
    kategori: Kategori | None


@dataclass(frozen=True)
class _HasilGrup:
    baris: list[_BarisHasil]
    pesan_gagal: str | None


def _ext_dari_path(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()


async def _muat_berkas(data_file: _DataFile) -> _Berkas:
    ext = _ext_dari_path(data_file.path)
    konten = await dapatkan_storage().baca(data_file.path)
    halaman = await asyncio.to_thread(hitung_halaman, konten, ext)
    return _Berkas(id_file=data_file.id_file, konten=konten, ext=ext, halaman=halaman)


def _buat_grup(berkas: list[_Berkas]) -> list[list[_Berkas]]:
    """Greedy menurut urutan unggah. File pertama sebuah grup selalu diterima;
    grup baru dimulai begitu menambah file berikutnya akan membuat total grup
    melebihi batas jumlah/ukuran/halaman."""
    grup: list[list[_Berkas]] = []
    saat_ini: list[_Berkas] = []
    ukuran = 0
    halaman = 0
    for b in berkas:
        if saat_ini and (
            len(saat_ini) + 1 > _MAKS_FILE_PER_GRUP
            or ukuran + b.ukuran > _MAKS_UKURAN_GRUP_BYTE
            or halaman + b.halaman > _MAKS_HALAMAN_GRUP
        ):
            grup.append(saat_ini)
            saat_ini, ukuran, halaman = [], 0, 0
        saat_ini.append(b)
        ukuran += b.ukuran
        halaman += b.halaman
    if saat_ini:
        grup.append(saat_ini)
    return grup


@asynccontextmanager
async def _buka_sesi(db: AsyncSession | None) -> AsyncGenerator[AsyncSession, None]:
    """Buka sesi DB pendek untuk satu fase. Di produksi (`db is None`), setiap
    fase membuka dan menutup sesi sendiri dari AsyncSessionLocal. Bila `db`
    disuntikkan oleh test, sesi itu dipakai ulang tanpa rollback setelah baca
    agar objek ORM milik test tidak kedaluwarsa."""
    if db is None:
        async with AsyncSessionLocal() as sesi:
            yield sesi
        return
    try:
        yield db
    except Exception:
        try:
            await db.rollback()
        except Exception as exc_rb:
            logger.error("pemrosesan_rollback_gagal tipe=%s", type(exc_rb).__name__)
        raise


async def _baca_data_awal(
    id_file_list: list[uuid.UUID], db: AsyncSession | None
) -> tuple[list[_DataFile], list[_DataSoal]] | None:
    """Fase 1: baca metadata File_Jawaban dan Soal pada sesi pendek lalu salin
    ke dataclass polos sebelum sesi ditutup."""
    async with _buka_sesi(db) as sesi:
        files = list(
            await sesi.scalars(
                select(FileJawaban)
                .where(FileJawaban.id_file.in_(id_file_list))
                .order_by(FileJawaban.diunggah_pada)
            )
        )
        if not files:
            return None
        data_files = [_DataFile(id_file=f.id_file, id_batch=f.id_batch, path=f.path) for f in files]
        id_batch = data_files[0].id_batch
        soal_rows = list(
            await sesi.scalars(select(Soal).where(Soal.id_batch == id_batch).order_by(Soal.no_soal))
        )
        data_soal = [
            _DataSoal(id_soal=s.id_soal, no_soal=s.no_soal, kunci_jawaban=s.kunci_jawaban)
            for s in soal_rows
        ]
    return data_files, data_soal


async def proses_file_jawaban(
    id_file_list: list[uuid.UUID], db: AsyncSession | None = None
) -> None:
    """Entry point BackgroundTasks. Membuka sesi DB pendek per fase sendiri
    (tidak memakai session request) kecuali `db` disediakan oleh test."""
    data_awal = await _baca_data_awal(id_file_list, db)
    if data_awal is None:
        return
    data_files, data_soal = data_awal

    try:
        berkas = []
        for f in data_files:
            berkas.append(await _muat_berkas(f))
    except Exception:
        logger.exception("pemrosesan_muat_berkas_gagal")
        await _tandai_id_gagal_aman([f.id_file for f in data_files], PESAN_GAGAL_UMUM, db)
        return

    for grup in _buat_grup(berkas):
        await _proses_satu_grup(grup, data_soal, db)


def _pesan_untuk(exc: Exception) -> str:
    if isinstance(exc, gemini.KuotaHarianHabis | gemini.GagalSementara):
        return PESAN_SIBUK_KUOTA
    return PESAN_GAGAL_UMUM


async def _proses_satu_grup(
    grup: list[_Berkas], soal_list: list[_DataSoal], db: AsyncSession | None
) -> None:
    """Jalankan fase Gemini (tanpa sesi DB) lalu fase simpan (sesi baru).
    Kegagalan tak terduga di sini ditandai gagal dengan pesan umum, tanpa
    memengaruhi grup lain."""
    id_files = [b.id_file for b in grup]
    try:
        hasil = await _jalankan_gemini_grup(grup, soal_list)
        await _simpan_hasil_grup(id_files, hasil, db)
    except DBAPIError as exc:
        orig_tipe = type(exc.orig).__name__ if exc.orig is not None else "none"
        logger.error(
            "pemrosesan_grup_gagal_db jumlah=%d tipe=%s orig=%s connection_invalidated=%s",
            len(id_files),
            type(exc).__name__,
            orig_tipe,
            exc.connection_invalidated,
        )
        await _tandai_id_gagal_aman(id_files, PESAN_GAGAL_UMUM, db)
    except Exception:
        logger.exception("pemrosesan_grup_gagal_tak_terduga")
        await _tandai_id_gagal_aman(id_files, PESAN_GAGAL_UMUM, db)


async def _jalankan_gemini_grup(grup: list[_Berkas], soal_list: list[_DataSoal]) -> _HasilGrup:
    """Fase 2: jalankan OCR dan judge untuk satu grup tanpa menyentuh DB."""
    no_soal_list = [s.no_soal for s in soal_list]
    try:
        hasil_ocr = await gemini.ocr_grup(
            [(b.konten, b.ext, i) for i, b in enumerate(grup)], no_soal_list
        )
    except (gemini.KuotaHarianHabis, gemini.GagalSementara, gemini.GagalPermanen) as exc:
        return _HasilGrup(baris=[], pesan_gagal=_pesan_untuk(exc))

    no_soal_valid = {s.no_soal for s in soal_list}
    teks_per_item: dict[str, str] = {}
    for item in hasil_ocr.items:
        file_index_str, pemisah, no_soal_str = item.id_item.partition(":")
        if not pemisah:
            continue
        try:
            file_index = int(file_index_str)
            no_soal = int(no_soal_str)
        except ValueError:
            continue
        if file_index < 0 or file_index >= len(grup) or no_soal not in no_soal_valid:
            continue
        key = f"{file_index}:{no_soal}"
        if key in teks_per_item:
            continue
        teks_per_item[key] = item.teks

    judge_items = [
        gemini.ItemJudgeMasuk(
            id_item=f"{i}:{s.no_soal}", kunci_jawaban=s.kunci_jawaban, teks_jawaban=teks
        )
        for i, _ in enumerate(grup)
        for s in soal_list
        if (teks := teks_per_item.get(f"{i}:{s.no_soal}", "")).strip()
    ]

    skor_per_item: dict[str, int] = {}
    judge_exc: Exception | None = None
    if judge_items:
        try:
            hasil_judge = await gemini.judge_grup(judge_items)
        except (gemini.KuotaHarianHabis, gemini.GagalSementara, gemini.GagalPermanen) as exc:
            judge_exc = exc
        else:
            id_item_diminta = {i.id_item for i in judge_items}
            for it in hasil_judge.items:
                if it.id_item not in id_item_diminta or it.id_item in skor_per_item:
                    continue
                if it.skor < 0 or it.skor > 100:
                    continue
                skor_per_item[it.id_item] = it.skor

    lengkap = True
    baris_list: list[_BarisHasil] = []
    for i, b in enumerate(grup):
        for s in soal_list:
            key = f"{i}:{s.no_soal}"
            teks = teks_per_item.get(key, "")
            if not teks.strip():
                teks_disimpan, skor, kategori = "", 0, Kategori.KURANG_MIRIP
            elif key in skor_per_item:
                skor = skor_per_item[key]
                teks_disimpan, kategori = teks, kategori_dari_skor(skor)
            else:
                teks_disimpan, skor, kategori = teks, None, None
                lengkap = False
            baris_list.append(
                _BarisHasil(
                    id_file=b.id_file,
                    id_soal=s.id_soal,
                    teks_ocr=teks_disimpan,
                    skor_sistem=skor,
                    kategori=kategori,
                )
            )

    if judge_exc is not None:
        return _HasilGrup(baris=baris_list, pesan_gagal=_pesan_untuk(judge_exc))
    if not lengkap:
        return _HasilGrup(baris=baris_list, pesan_gagal=PESAN_GAGAL_UMUM)
    return _HasilGrup(baris=baris_list, pesan_gagal=None)


async def _simpan_hasil_grup(
    id_files: list[uuid.UUID], hasil: _HasilGrup, db: AsyncSession | None
) -> None:
    """Fase 3: buka sesi baru untuk menyimpan Hasil_Koreksi dan status grup."""
    async with _buka_sesi(db) as sesi:
        ada_files = set(
            await sesi.scalars(select(FileJawaban.id_file).where(FileJawaban.id_file.in_(id_files)))
        )
        if not ada_files:
            logger.warning("pemrosesan_simpan_baris_hilang jumlah=%d", len(id_files))
            if sesi.in_transaction():
                await sesi.rollback()
            return

        for baris in hasil.baris:
            await _upsert_hasil(
                sesi,
                baris.id_file,
                baris.id_soal,
                baris.teks_ocr,
                baris.skor_sistem,
                baris.kategori,
            )

        if hasil.pesan_gagal is not None:
            status_baru, pesan_error = StatusProses.GAGAL, hasil.pesan_gagal
        else:
            status_baru, pesan_error = StatusProses.SELESAI, None

        await sesi.execute(
            update(FileJawaban)
            .where(FileJawaban.id_file.in_(id_files))
            .values(status_proses=status_baru, pesan_error=pesan_error)
        )
        await sesi.commit()


async def _upsert_hasil(
    db: AsyncSession,
    id_file: uuid.UUID,
    id_soal: uuid.UUID,
    teks_ocr: str,
    skor: int | None,
    kategori: Kategori | None,
) -> None:
    stmt = (
        pg_insert(HasilKoreksi)
        .values(
            id_file=id_file,
            id_soal=id_soal,
            teks_ocr=teks_ocr,
            skor_sistem=skor,
            kategori=kategori,
        )
        .on_conflict_do_update(
            index_elements=["id_file", "id_soal"],
            set_={"teks_ocr": teks_ocr, "skor_sistem": skor, "kategori": kategori},
        )
    )
    await db.execute(stmt)


async def _tandai_id_gagal_aman(
    id_files: list[uuid.UUID], pesan: str, db: AsyncSession | None
) -> None:
    """Tandai daftar id_file sebagai gagal di sesi baru. Tidak pernah melempar:
    bila baris sudah hilang (batch dihapus lewat request lain, FR22), UPDATE
    memengaruhi 0 baris tanpa error; bila DB tidak terjangkau, catat log aman
    tanpa parameter SQL lalu lanjut ke grup berikutnya (baris yang tertinggal
    'diproses' akan disapu sapu_proses_tergantung saat server dimulai ulang)."""
    try:
        async with _buka_sesi(db) as sesi:
            await sesi.execute(
                update(FileJawaban)
                .where(FileJawaban.id_file.in_(id_files))
                .values(status_proses=StatusProses.GAGAL, pesan_error=pesan)
            )
            await sesi.commit()
    except Exception as exc:
        orig = getattr(exc, "orig", None)
        orig_tipe = type(orig).__name__ if orig is not None else "none"
        logger.error(
            "pemrosesan_tandai_gagal_error jumlah=%d tipe=%s orig=%s",
            len(id_files),
            type(exc).__name__,
            orig_tipe,
        )
