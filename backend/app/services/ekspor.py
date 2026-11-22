import asyncio
import logging
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

import xlsxwriter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.enums import Kategori, StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services.batch import ambil_batch
from app.services.langganan import jenis_akun_efektif

logger = logging.getLogger(__name__)

MEDIA_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

EKSPOR_KHUSUS_PRO = AppError(
    kode="EKSPOR_KHUSUS_PRO",
    pesan="Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini.",
    status_code=403,
)
BATCH_BELUM_ADA_JAWABAN = AppError(
    kode="BATCH_BELUM_ADA_JAWABAN",
    pesan="Belum ada jawaban peserta didik pada batch ini untuk diekspor.",
    status_code=400,
)
GAGAL_EKSPOR = AppError(
    kode="GAGAL_EKSPOR",
    pesan="Gagal membuat file ekspor, silakan coba lagi",
    status_code=500,
)

# Offset tetap WIB (UTC+7) tanpa ketergantungan tzdata di container slim.
_TZ_WIB = timezone(timedelta(hours=7))
_MAKS_PANJANG_SLUG = 80
_REGEX_BUKAN_AMAN = re.compile(r"[^a-z0-9]+")
_AWALAN_FORMULA = ("=", "+", "-", "@", "\t", "\r")

_LABEL_STATUS: dict[StatusProses, str] = {
    StatusProses.SELESAI: "Selesai",
    StatusProses.DIPROSES: "Diproses",
    StatusProses.GAGAL: "Gagal",
}
_LABEL_KATEGORI: dict[Kategori, str] = {
    Kategori.SANGAT_MIRIP: "Sangat Mirip",
    Kategori.CUKUP_MIRIP: "Cukup Mirip",
    Kategori.KURANG_MIRIP: "Kurang Mirip",
}


@dataclass(frozen=True)
class NilaiSoalEkspor:
    skor_sistem: int | None
    kategori: Kategori | None
    skor_revisi: int | None


@dataclass(frozen=True)
class BarisPesertaEkspor:
    nama_peserta_didik: str | None
    status_proses: StatusProses
    nilai_per_soal: tuple[NilaiSoalEkspor | None, ...]


@dataclass(frozen=True)
class DataEkspor:
    nama_batch: str
    daftar_no_soal: tuple[int, ...]
    baris_peserta: tuple[BarisPesertaEkspor, ...]


def sanitasi_nama_batch(nama_batch: str) -> str:
    """Bersihkan nama batch menjadi slug ASCII aman untuk nama berkas dan header HTTP."""
    normal = unicodedata.normalize("NFKD", nama_batch).encode("ascii", "ignore").decode("ascii")
    slug = _REGEX_BUKAN_AMAN.sub("-", normal.lower()).strip("-")
    if len(slug) > _MAKS_PANJANG_SLUG:
        slug = slug[:_MAKS_PANJANG_SLUG].rstrip("-")
    return slug or "batch"


def buat_nama_file_ekspor(nama_batch: str, tanggal: date | None = None) -> str:
    """Bentuk nama file rekap-nilai-<nama batch>-<yyyy-mm-dd>.xlsx dengan karakter aman."""
    tgl = tanggal if tanggal is not None else datetime.now(_TZ_WIB).date()
    return f"rekap-nilai-{sanitasi_nama_batch(nama_batch)}-{tgl.isoformat()}.xlsx"


def _perlu_quote_prefix(teks: str) -> bool:
    """Deteksi string berawalan pemicu formula (=, +, -, @, tab, CR), termasuk setelah spasi."""
    if not teks:
        return False
    if teks.startswith(_AWALAN_FORMULA):
        return True
    terpotong = teks.lstrip()
    return bool(terpotong) and terpotong.startswith(_AWALAN_FORMULA)


def _tulis_sel_teks(
    ws: xlsxwriter.worksheet.Worksheet,
    row: int,
    col: int,
    nilai: str | None,
    fmt_teks: xlsxwriter.format.Format,
    fmt_teks_aman: xlsxwriter.format.Format,
) -> None:
    """Tulis teks asal pengguna sebagai string OOXML biasa, bukan formula.
    Nilai kosong/None dibiarkan kosong, selaras dengan tampilan daftar di UI."""
    teks = nilai or ""
    if teks == "":
        ws.write_blank(row, col, None, fmt_teks)
        return
    fmt = fmt_teks_aman if _perlu_quote_prefix(teks) else fmt_teks
    ws.write_string(row, col, teks, fmt)


def _bangun_workbook_bytes(data: DataEkspor) -> bytes:
    """Bangun berkas .xlsx 'Rekap Nilai' di memori. Fungsi sinkron murni untuk
    dijalankan lewat asyncio.to_thread tanpa menyentuh session database."""
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(
        buffer,
        {
            "in_memory": True,
            "strings_to_formulas": False,
            "strings_to_urls": False,
            "strings_to_numbers": False,
        },
    )
    try:
        ws = workbook.add_worksheet("Rekap Nilai")

        fmt_header = workbook.add_format(
            {"bold": True, "align": "center", "valign": "vcenter", "border": 1}
        )
        fmt_subheader = workbook.add_format(
            {"bold": True, "align": "center", "valign": "vcenter", "border": 1}
        )
        fmt_teks = workbook.add_format({"num_format": "@", "valign": "vcenter"})
        fmt_teks_aman = workbook.add_format(
            {"num_format": "@", "quote_prefix": True, "valign": "vcenter"}
        )
        fmt_tengah = workbook.add_format({"align": "center", "valign": "vcenter"})
        fmt_angka = workbook.add_format({"num_format": "0", "align": "center", "valign": "vcenter"})
        fmt_rata_rata = workbook.add_format(
            {"num_format": "0.00", "align": "center", "valign": "vcenter"}
        )

        # Header 2 baris: No, Nama Peserta Didik, Status, tiap Soal N (3 subkolom), Rata-rata.
        ws.merge_range(0, 0, 1, 0, "No", fmt_header)
        ws.merge_range(0, 1, 1, 1, "Nama Peserta Didik", fmt_header)
        ws.merge_range(0, 2, 1, 2, "Status", fmt_header)

        ws.set_column(0, 0, 6)
        ws.set_column(1, 1, 28)
        ws.set_column(2, 2, 12)

        for indeks_soal, no_soal in enumerate(data.daftar_no_soal):
            col_awal = 3 + indeks_soal * 3
            ws.merge_range(0, col_awal, 0, col_awal + 2, f"Soal {no_soal}", fmt_header)
            ws.write_string(1, col_awal, "Skor", fmt_subheader)
            ws.write_string(1, col_awal + 1, "Kategori", fmt_subheader)
            ws.write_string(1, col_awal + 2, "Nilai Akhir", fmt_subheader)
            ws.set_column(col_awal, col_awal, 9)
            ws.set_column(col_awal + 1, col_awal + 1, 15)
            ws.set_column(col_awal + 2, col_awal + 2, 12)

        col_rata = 3 + len(data.daftar_no_soal) * 3
        ws.merge_range(0, col_rata, 1, col_rata, "Rata-rata", fmt_header)
        ws.set_column(col_rata, col_rata, 12)

        for indeks_baris, peserta in enumerate(data.baris_peserta):
            row = 2 + indeks_baris
            ws.write_number(row, 0, indeks_baris + 1, fmt_angka)
            _tulis_sel_teks(ws, row, 1, peserta.nama_peserta_didik, fmt_teks, fmt_teks_aman)
            ws.write_string(row, 2, _LABEL_STATUS[peserta.status_proses], fmt_tengah)

            # Baris Diproses/Gagal tetap tampil dengan seluruh sel nilai kosong.
            if peserta.status_proses != StatusProses.SELESAI:
                continue

            nilai_terhitung = []
            for indeks_soal, nilai_soal in enumerate(peserta.nilai_per_soal):
                if nilai_soal is None:
                    continue
                col_awal = 3 + indeks_soal * 3
                if nilai_soal.skor_sistem is not None:
                    ws.write_number(row, col_awal, nilai_soal.skor_sistem, fmt_angka)
                if nilai_soal.kategori is not None:
                    ws.write_string(
                        row, col_awal + 1, _LABEL_KATEGORI[nilai_soal.kategori], fmt_tengah
                    )
                if nilai_soal.skor_revisi is not None:
                    ws.write_number(row, col_awal + 2, nilai_soal.skor_revisi, fmt_angka)

                skor_efektif = (
                    nilai_soal.skor_revisi
                    if nilai_soal.skor_revisi is not None
                    else nilai_soal.skor_sistem
                )
                if skor_efektif is not None:
                    nilai_terhitung.append(skor_efektif)

            if nilai_terhitung:
                rata_rata = round(sum(nilai_terhitung) / len(nilai_terhitung), 2)
                ws.write_number(row, col_rata, rata_rata, fmt_rata_rata)
    finally:
        workbook.close()

    return buffer.getvalue()


async def ekspor_rekap_nilai(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID
) -> tuple[bytes, str]:
    """FR17/F-EKSPOR: hasilkan file rekap nilai .xlsx untuk satu batch (khusus akun Pro).
    Mengembalikan pasangan (konten_xlsx_bytes, nama_file)."""
    if jenis_akun_efektif(pengguna) != StatusLangganan.PRO:
        raise EKSPOR_KHUSUS_PRO

    batch = await ambil_batch(db, pengguna, id_batch)

    soal_list = list(
        await db.scalars(
            select(Soal).where(Soal.id_batch == batch.id_batch).order_by(Soal.no_soal.asc())
        )
    )
    file_jawaban_list = list(
        await db.scalars(
            select(FileJawaban)
            .where(FileJawaban.id_batch == batch.id_batch)
            .order_by(FileJawaban.diunggah_pada.asc(), FileJawaban.id_file.asc())
        )
    )
    if not file_jawaban_list:
        raise BATCH_BELUM_ADA_JAWABAN

    id_file_selesai = [
        fj.id_file for fj in file_jawaban_list if fj.status_proses == StatusProses.SELESAI
    ]
    peta_hasil: dict[tuple[uuid.UUID, uuid.UUID], NilaiSoalEkspor] = {}
    if id_file_selesai:
        hasil_rows = await db.scalars(
            select(HasilKoreksi).where(HasilKoreksi.id_file.in_(id_file_selesai))
        )
        for baris in hasil_rows:
            peta_hasil[(baris.id_file, baris.id_soal)] = NilaiSoalEkspor(
                skor_sistem=baris.skor_sistem,
                kategori=baris.kategori,
                skor_revisi=baris.skor_revisi,
            )

    # Salin seluruh data ORM (termasuk batch.nama_batch) ke struktur polos
    # sebelum mengakhiri transaksi baca, agar tidak ada akses atribut ORM
    # setelah rollback (mencegah MissingGreenlet) maupun lintas thread.
    nama_batch = batch.nama_batch
    id_batch_val = batch.id_batch
    daftar_soal_id = [soal.id_soal for soal in soal_list]
    daftar_no_soal = tuple(soal.no_soal for soal in soal_list)
    baris_peserta = tuple(
        BarisPesertaEkspor(
            nama_peserta_didik=fj.nama_peserta_didik,
            status_proses=fj.status_proses,
            nilai_per_soal=(
                tuple(peta_hasil.get((fj.id_file, id_soal)) for id_soal in daftar_soal_id)
                if fj.status_proses == StatusProses.SELESAI
                else tuple(None for _ in daftar_soal_id)
            ),
        )
        for fj in file_jawaban_list
    )
    data_ekspor = DataEkspor(
        nama_batch=nama_batch,
        daftar_no_soal=daftar_no_soal,
        baris_peserta=baris_peserta,
    )
    await db.rollback()

    try:
        konten = await asyncio.to_thread(_bangun_workbook_bytes, data_ekspor)
    except Exception as exc:
        logger.error(
            "ekspor_rekap_gagal id_batch=%s tipe=%s",
            id_batch_val,
            type(exc).__name__,
        )
        raise GAGAL_EKSPOR from None

    nama_file = buat_nama_file_ekspor(data_ekspor.nama_batch)
    return konten, nama_file
