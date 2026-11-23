from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta, timezone

from app.models.enums import PaketLangganan, StatusLangganan
from app.models.pengguna import Pengguna

# Offset tetap WIB (UTC+7) tanpa ketergantungan tzdata di container slim.
TZ_WIB = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class BatasAkun:
    maks_batch_aktif: int | None
    maks_soal_per_batch: int
    maks_jawaban_per_batch: int


# Angka batas di bawah harus sama persis dengan tabel batas di docs/SPEC.md bagian 4
# (dan frontend/src/api/pesan.js).
BATAS_PER_JENIS_AKUN: dict[StatusLangganan, BatasAkun] = {
    StatusLangganan.FREE: BatasAkun(
        maks_batch_aktif=1,
        maks_soal_per_batch=15,
        maks_jawaban_per_batch=15,
    ),
    StatusLangganan.PRO: BatasAkun(
        maks_batch_aktif=None,
        maks_soal_per_batch=30,
        maks_jawaban_per_batch=50,
    ),
}


def jenis_akun_efektif(pengguna: Pengguna, sekarang: datetime | None = None) -> StatusLangganan:
    """Kembalikan jenis akun yang berlaku saat ini; Pro yang masa_berlaku_pro-nya
    sudah lewat diperlakukan sebagai Free."""
    if pengguna.status_langganan != StatusLangganan.PRO:
        return StatusLangganan.FREE
    waktu = sekarang if sekarang is not None else datetime.now(UTC)
    if pengguna.masa_berlaku_pro is not None and pengguna.masa_berlaku_pro <= waktu:
        return StatusLangganan.FREE
    return StatusLangganan.PRO


def batas_untuk_pengguna(pengguna: Pengguna) -> BatasAkun:
    return BATAS_PER_JENIS_AKUN[jenis_akun_efektif(pengguna)]


# Harga dan durasi paket harus sama persis dengan docs/SPEC.md bagian 9 (F-LANGGANAN,
# U10): 1 bulan = 30 hari tetap, 3 bulan = 90 hari tetap (bukan bulan kalender).
HARGA_PAKET: dict[PaketLangganan, int] = {
    PaketLangganan.PRO_1_BULAN: 30_000,
    PaketLangganan.PRO_3_BULAN: 80_000,
}

DURASI_HARI_PAKET: dict[PaketLangganan, int] = {
    PaketLangganan.PRO_1_BULAN: 30,
    PaketLangganan.PRO_3_BULAN: 90,
}


def hitung_masa_berlaku_baru(
    pengguna: Pengguna, paket: PaketLangganan, sekarang: datetime
) -> datetime:
    """Masa berlaku Pro baru setelah pembayaran dikonfirmasi.

    Pro yang masih berlaku DAN punya masa_berlaku_pro jelas: masa berlaku baru =
    masa berlaku saat ini + durasi paket (perpanjangan manual, U8/changelog
    2026-11-01). Selain itu (Free, Pro kedaluwarsa, atau Pro aktif tapi
    masa_berlaku_pro NULL -- misal diset permanen lewat FR25 Admin tanpa tanggal):
    dihitung dari sekarang, dibulatkan ke 23:59:59 WIB pada hari jatuh tempo.
    """
    durasi = timedelta(days=DURASI_HARI_PAKET[paket])
    if (
        jenis_akun_efektif(pengguna, sekarang) == StatusLangganan.PRO
        and pengguna.masa_berlaku_pro is not None
    ):
        return pengguna.masa_berlaku_pro + durasi

    tanggal_akhir_wib = (sekarang.astimezone(TZ_WIB) + durasi).date()
    akhir_hari_wib = datetime.combine(tanggal_akhir_wib, time(23, 59, 59), tzinfo=TZ_WIB)
    return akhir_hari_wib.astimezone(UTC)
