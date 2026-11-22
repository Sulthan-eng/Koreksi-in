from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from app.models.enums import StatusLangganan
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
