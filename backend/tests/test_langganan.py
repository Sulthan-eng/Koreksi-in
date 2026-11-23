import uuid
from datetime import UTC, datetime, timedelta

from app.models.enums import PaketLangganan, Peran, StatusLangganan
from app.models.pengguna import Pengguna
from app.services.langganan import TZ_WIB, hitung_masa_berlaku_baru


def _pengguna(
    *, status_langganan: StatusLangganan = StatusLangganan.FREE, masa_berlaku_pro=None
) -> Pengguna:
    return Pengguna(
        id_pengguna=uuid.uuid4(),
        nama="Pengajar Test",
        email="pengajar@contoh.id",
        password_hash="x",
        peran=Peran.PENGAJAR,
        status_langganan=status_langganan,
        masa_berlaku_pro=masa_berlaku_pro,
    )


def test_free_dihitung_dari_sekarang_dibulatkan_akhir_hari_wib() -> None:
    pengguna = _pengguna(status_langganan=StatusLangganan.FREE)
    sekarang = datetime(2026, 11, 23, 10, 0, 0, tzinfo=UTC)

    hasil = hitung_masa_berlaku_baru(pengguna, PaketLangganan.PRO_1_BULAN, sekarang)

    tanggal_wib = sekarang.astimezone(TZ_WIB).date() + timedelta(days=30)
    hasil_wib = hasil.astimezone(TZ_WIB)
    assert hasil_wib.date() == tanggal_wib
    assert (hasil_wib.hour, hasil_wib.minute, hasil_wib.second) == (23, 59, 59)


def test_pro_kedaluwarsa_dihitung_dari_sekarang() -> None:
    sekarang = datetime(2026, 11, 23, 10, 0, 0, tzinfo=UTC)
    pengguna = _pengguna(
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang - timedelta(days=1),
    )

    hasil = hitung_masa_berlaku_baru(pengguna, PaketLangganan.PRO_1_BULAN, sekarang)

    tanggal_wib = sekarang.astimezone(TZ_WIB).date() + timedelta(days=30)
    assert hasil.astimezone(TZ_WIB).date() == tanggal_wib


def test_pro_aktif_tanpa_masa_berlaku_dihitung_dari_sekarang() -> None:
    """Pro aktif tapi masa_berlaku_pro NULL (misal diset permanen lewat FR25
    Admin tanpa tanggal): dihitung dari sekarang, bukan error."""
    sekarang = datetime(2026, 11, 23, 10, 0, 0, tzinfo=UTC)
    pengguna = _pengguna(status_langganan=StatusLangganan.PRO, masa_berlaku_pro=None)

    hasil = hitung_masa_berlaku_baru(pengguna, PaketLangganan.PRO_3_BULAN, sekarang)

    tanggal_wib = sekarang.astimezone(TZ_WIB).date() + timedelta(days=90)
    hasil_wib = hasil.astimezone(TZ_WIB)
    assert hasil_wib.date() == tanggal_wib
    assert (hasil_wib.hour, hasil_wib.minute, hasil_wib.second) == (23, 59, 59)


def test_pro_masih_berlaku_ditambah_dari_masa_berlaku_saat_ini() -> None:
    sekarang = datetime(2026, 11, 23, 10, 0, 0, tzinfo=UTC)
    masa_berlaku_saat_ini = sekarang + timedelta(days=10)
    pengguna = _pengguna(
        status_langganan=StatusLangganan.PRO, masa_berlaku_pro=masa_berlaku_saat_ini
    )

    hasil = hitung_masa_berlaku_baru(pengguna, PaketLangganan.PRO_1_BULAN, sekarang)

    assert hasil == masa_berlaku_saat_ini + timedelta(days=30)


def test_perpanjangan_lintas_akhir_bulan() -> None:
    sekarang = datetime(2026, 11, 23, 10, 0, 0, tzinfo=UTC)
    # 23:59:59 WIB 20 Des 2026 (sudah lewat akhir November/Desember).
    masa_berlaku_saat_ini = datetime(2026, 12, 20, 16, 59, 59, tzinfo=UTC)
    pengguna = _pengguna(
        status_langganan=StatusLangganan.PRO, masa_berlaku_pro=masa_berlaku_saat_ini
    )

    hasil = hitung_masa_berlaku_baru(pengguna, PaketLangganan.PRO_3_BULAN, sekarang)

    assert hasil == masa_berlaku_saat_ini + timedelta(days=90)
    hasil_wib = hasil.astimezone(TZ_WIB)
    assert (hasil_wib.hour, hasil_wib.minute, hasil_wib.second) == (23, 59, 59)
