import uuid

from sqlalchemy import Row, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.enums import StatusBatch, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import gemini
from app.services.batch import BATCH_SUDAH_SELESAI, ambil_batch
from app.services.pemrosesan import kategori_dari_skor

TEKS_OCR_KOSONG = AppError(
    kode="TEKS_OCR_KOSONG", pesan="Teks jawaban tidak boleh kosong", status_code=400
)
TEKS_OCR_TERLALU_PANJANG = AppError(
    kode="TEKS_OCR_TERLALU_PANJANG",
    pesan="Teks jawaban maksimal 10.000 karakter.",
    status_code=400,
)
HASIL_KOREKSI_TIDAK_DITEMUKAN = AppError(
    kode="HASIL_KOREKSI_TIDAK_DITEMUKAN", pesan="Hasil koreksi tidak ditemukan.", status_code=404
)
NILAI_AKHIR_TIDAK_VALID = AppError(
    kode="NILAI_AKHIR_TIDAK_VALID",
    pesan="Nilai akhir harus bilangan bulat 0 sampai 100.",
    status_code=400,
)
GAGAL_SIMPAN_NILAI_AKHIR = AppError(
    kode="GAGAL_SIMPAN_NILAI_AKHIR",
    pesan="Nilai gagal disimpan, silakan mencoba menyimpan kembali.",
    status_code=500,
)

_MAKS_PANJANG_TEKS_OCR = 10_000


async def daftar_hasil_koreksi(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID
) -> list[Row]:
    batch = await ambil_batch(db, pengguna, id_batch)
    hasil = await db.execute(
        select(
            HasilKoreksi.id_koreksi,
            FileJawaban.id_file,
            FileJawaban.nama_peserta_didik,
            Soal.no_soal,
            HasilKoreksi.teks_ocr,
            HasilKoreksi.skor_sistem,
            HasilKoreksi.kategori,
            HasilKoreksi.skor_revisi,
            HasilKoreksi.skor_hitung_ulang,
        )
        .join(HasilKoreksi, HasilKoreksi.id_file == FileJawaban.id_file)
        .join(Soal, Soal.id_soal == HasilKoreksi.id_soal)
        .where(
            FileJawaban.id_batch == batch.id_batch,
            FileJawaban.status_proses == StatusProses.SELESAI,
        )
        .order_by(FileJawaban.diunggah_pada.asc(), Soal.no_soal.asc())
    )
    return list(hasil.all())


async def edit_teks_ocr(
    db: AsyncSession,
    pengguna: Pengguna,
    id_batch: uuid.UUID,
    id_koreksi: uuid.UUID,
    teks_ocr: str,
) -> HasilKoreksi:
    """FR15/F-EDIT-OCR: edit teks_ocr satu baris Hasil_Koreksi dan hitung ulang
    skor lewat judge. Lihat SPEC bagian 9 untuk aturan lengkap."""
    teks_trim = teks_ocr.strip()
    if not teks_trim:
        raise TEKS_OCR_KOSONG
    if len(teks_trim) > _MAKS_PANJANG_TEKS_OCR:
        raise TEKS_OCR_TERLALU_PANJANG

    batch = await ambil_batch(db, pengguna, id_batch)
    if batch.status == StatusBatch.SELESAI:
        raise BATCH_SUDAH_SELESAI

    baris = await db.scalar(
        select(HasilKoreksi)
        .join(FileJawaban, FileJawaban.id_file == HasilKoreksi.id_file)
        .where(
            HasilKoreksi.id_koreksi == id_koreksi,
            FileJawaban.id_batch == batch.id_batch,
            FileJawaban.status_proses == StatusProses.SELESAI,
        )
    )
    if baris is None:
        raise HASIL_KOREKSI_TIDAK_DITEMUKAN

    if teks_trim == baris.teks_ocr.strip() and not baris.skor_hitung_ulang:
        return baris

    soal = await db.get(Soal, baris.id_soal)

    baris.teks_ocr = teks_trim
    baris.skor_hitung_ulang = True
    await db.commit()

    skor: int | None = None
    try:
        hasil_judge = await gemini.judge_grup(
            [
                gemini.ItemJudgeMasuk(
                    id_item=str(id_koreksi),
                    kunci_jawaban=soal.kunci_jawaban,
                    teks_jawaban=teks_trim,
                )
            ]
        )
    except (gemini.KuotaHarianHabis, gemini.GagalSementara, gemini.GagalPermanen):
        hasil_judge = None

    if hasil_judge is not None:
        for item in hasil_judge.items:
            if item.id_item == str(id_koreksi) and 0 <= item.skor <= 100:
                skor = item.skor
                break

    if skor is not None:
        kategori = kategori_dari_skor(skor)
        await db.execute(
            update(HasilKoreksi)
            .where(HasilKoreksi.id_koreksi == id_koreksi, HasilKoreksi.teks_ocr == teks_trim)
            .values(skor_sistem=skor, kategori=kategori, skor_hitung_ulang=False)
        )
        await db.commit()

    baris_terbaru = await db.get(HasilKoreksi, id_koreksi, populate_existing=True)
    if baris_terbaru is None:
        raise HASIL_KOREKSI_TIDAK_DITEMUKAN
    return baris_terbaru


async def ubah_nilai_akhir(
    db: AsyncSession,
    pengguna: Pengguna,
    id_batch: uuid.UUID,
    id_koreksi: uuid.UUID,
    skor_revisi: object,
) -> HasilKoreksi:
    """FR16/F-NILAI: tetapkan Nilai Akhir manual (skor_revisi) satu baris
    Hasil_Koreksi. Tidak menyentuh skor_sistem, kategori, teks_ocr, atau
    skor_hitung_ulang. Lihat SPEC bagian 9 untuk aturan lengkap."""
    if not isinstance(skor_revisi, int) or isinstance(skor_revisi, bool):
        raise NILAI_AKHIR_TIDAK_VALID
    if not (0 <= skor_revisi <= 100):
        raise NILAI_AKHIR_TIDAK_VALID

    batch = await ambil_batch(db, pengguna, id_batch)
    if batch.status == StatusBatch.SELESAI:
        raise BATCH_SUDAH_SELESAI

    baris = await db.scalar(
        select(HasilKoreksi)
        .join(FileJawaban, FileJawaban.id_file == HasilKoreksi.id_file)
        .where(
            HasilKoreksi.id_koreksi == id_koreksi,
            FileJawaban.id_batch == batch.id_batch,
            FileJawaban.status_proses == StatusProses.SELESAI,
        )
    )
    if baris is None:
        raise HASIL_KOREKSI_TIDAK_DITEMUKAN

    baris.skor_revisi = skor_revisi
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_SIMPAN_NILAI_AKHIR from None
    return baris
