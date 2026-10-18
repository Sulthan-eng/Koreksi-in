"""Pengelompokan file, pipeline OCR lalu judge per grup, dan penyimpanan
Hasil_Koreksi (SPEC bagian 8). Dipanggil lewat BackgroundTasks setelah unggah."""

import logging
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.enums import Kategori, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.soal import Soal
from app.services import gemini
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


class _Berkas:
    def __init__(self, row: FileJawaban, konten: bytes, ext: str, halaman: int) -> None:
        self.row = row
        self.konten = konten
        self.ext = ext
        self.ukuran = len(konten)
        self.halaman = halaman


def _ext_dari_path(path: str) -> str:
    return path.rsplit(".", 1)[-1].lower()


def _muat_berkas(row: FileJawaban) -> _Berkas:
    konten = (Path(settings.UPLOAD_DIR) / row.path).read_bytes()
    ext = _ext_dari_path(row.path)
    return _Berkas(row=row, konten=konten, ext=ext, halaman=hitung_halaman(konten, ext))


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


async def proses_file_jawaban(
    id_file_list: list[uuid.UUID], db: AsyncSession | None = None
) -> None:
    """Entry point BackgroundTasks. Membuka session sendiri (tidak memakai session request)
    kecuali `db` disediakan (dipakai test agar tidak menyentuh database pengembangan)."""
    if db is None:
        async with AsyncSessionLocal() as sesi_baru:
            await _proses_file_jawaban_dengan_sesi(id_file_list, sesi_baru)
        return
    await _proses_file_jawaban_dengan_sesi(id_file_list, db)


async def _proses_file_jawaban_dengan_sesi(id_file_list: list[uuid.UUID], db: AsyncSession) -> None:
    files = list(
        await db.scalars(
            select(FileJawaban)
            .where(FileJawaban.id_file.in_(id_file_list))
            .order_by(FileJawaban.diunggah_pada)
        )
    )
    if not files:
        return
    id_batch = files[0].id_batch
    soal_list = list(
        await db.scalars(select(Soal).where(Soal.id_batch == id_batch).order_by(Soal.no_soal))
    )
    berkas = [_muat_berkas(f) for f in files]
    for grup in _buat_grup(berkas):
        try:
            await _proses_satu_grup(db, grup, soal_list)
        except Exception:
            logger.exception("pemrosesan_grup_gagal_tak_terduga")
            await db.rollback()
            await _tandai_gagal(db, grup, PESAN_GAGAL_UMUM)


def _pesan_untuk(exc: Exception) -> str:
    if isinstance(exc, gemini.KuotaHarianHabis | gemini.GagalSementara):
        return PESAN_SIBUK_KUOTA
    return PESAN_GAGAL_UMUM


async def _proses_satu_grup(db: AsyncSession, grup: list[_Berkas], soal_list: list[Soal]) -> None:
    """Jaring pengaman terluar: kegagalan tak terduga di sini ditandai gagal
    dengan pesan umum, tanpa memengaruhi grup lain."""
    try:
        await _proses_satu_grup_inner(db, grup, soal_list)
    except Exception:
        logger.exception("pemrosesan_grup_gagal_tak_terduga")
        await db.rollback()
        await _tandai_gagal(db, grup, PESAN_GAGAL_UMUM)


async def _proses_satu_grup_inner(
    db: AsyncSession, grup: list[_Berkas], soal_list: list[Soal]
) -> None:
    no_soal_list = [s.no_soal for s in soal_list]
    try:
        hasil_ocr = await gemini.ocr_grup(
            [(b.konten, b.ext, i) for i, b in enumerate(grup)], no_soal_list
        )
    except (gemini.KuotaHarianHabis, gemini.GagalSementara, gemini.GagalPermanen) as exc:
        await _tandai_gagal(db, grup, _pesan_untuk(exc))
        return

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
            await _upsert_hasil(db, b.row.id_file, s.id_soal, teks_disimpan, skor, kategori)

    if judge_exc is not None:
        await _tandai_gagal(db, grup, _pesan_untuk(judge_exc))
        return
    if not lengkap:
        await _tandai_gagal(db, grup, PESAN_GAGAL_UMUM)
        return

    for b in grup:
        b.row.status_proses = StatusProses.SELESAI
        b.row.pesan_error = None
    await db.commit()


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


async def _tandai_gagal(db: AsyncSession, grup: list[_Berkas], pesan: str) -> None:
    for b in grup:
        b.row.status_proses = StatusProses.GAGAL
        b.row.pesan_error = pesan
    await db.commit()
