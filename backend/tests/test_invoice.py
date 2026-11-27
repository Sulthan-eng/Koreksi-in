from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import PaketLangganan, Peran, StatusTransaksi
from app.models.pengguna import Pengguna
from app.models.transaksi_pembayaran import TransaksiPembayaran
from app.services import email_templates
from app.services import transaksi as transaksi_service


async def _buat_pengguna(
    db_session: AsyncSession,
    *,
    nama: str,
    email: str,
    password: str = "rahasia123",
    peran: Peran = Peran.PENGAJAR,
) -> Pengguna:
    pengguna = Pengguna(
        nama=nama, email=email, password_hash=await hash_password(password), peran=peran
    )
    db_session.add(pengguna)
    await db_session.commit()
    await db_session.refresh(pengguna)
    return pengguna


async def _masuk(client: AsyncClient, email: str, password: str = "rahasia123") -> str:
    response = await client.post("/api/auth/masuk", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _token_pengajar(
    client: AsyncClient, db_session: AsyncSession, email: str = "pengajar@contoh.id"
) -> dict[str, str]:
    await _buat_pengguna(db_session, nama="Pengajar Test", email=email)
    token = await _masuk(client, email)
    return {"Authorization": f"Bearer {token}"}


async def _buat_transaksi(
    db_session: AsyncSession,
    pengguna: Pengguna,
    *,
    id_order: str,
    status: StatusTransaksi = StatusTransaksi.BERHASIL,
    paket: PaketLangganan = PaketLangganan.PRO_1_BULAN,
    nominal: int = 30000,
    metode_pembayaran: str | None = "Transfer Bank",
) -> TransaksiPembayaran:
    transaksi = TransaksiPembayaran(
        id_pengguna=pengguna.id_pengguna,
        id_order=id_order,
        paket=paket,
        nominal=nominal,
        status=status,
        diperbarui_pada=datetime.now(UTC),
        metode_pembayaran=metode_pembayaran,
    )
    db_session.add(transaksi)
    await db_session.commit()
    await db_session.refresh(transaksi)
    return transaksi


def test_petakan_metode_dikenal() -> None:
    assert transaksi_service._petakan_metode("bank_transfer") == "Transfer Bank"
    assert transaksi_service._petakan_metode("credit_card") == "Kartu Kredit/Debit"
    assert transaksi_service._petakan_metode("qris") == "QRIS"


def test_petakan_metode_tidak_dikenal_disimpan_mentah() -> None:
    assert transaksi_service._petakan_metode("metode_baru_dari_midtrans") == (
        "metode_baru_dari_midtrans"
    )


def test_petakan_metode_kosong_atau_bukan_string() -> None:
    assert transaksi_service._petakan_metode(None) is None
    assert transaksi_service._petakan_metode("") is None
    assert transaksi_service._petakan_metode(123) is None


def test_format_tanggal_wib_selisih_tetap_utc_plus_7() -> None:
    waktu_utc = datetime(2026, 11, 27, 3, 46, tzinfo=UTC)
    assert email_templates.format_tanggal_wib(waktu_utc) == "27 November 2026, 10.46 WIB"

    # Lewat 17.00 UTC berpindah hari di WIB (00.00 WIB hari berikutnya)
    batas_hari = datetime(2026, 11, 26, 17, 0, tzinfo=UTC)
    assert email_templates.format_tanggal_wib(batas_hari) == "27 November 2026, 00.00 WIB"

    # Datetime naive diperlakukan sebagai UTC
    waktu_naive = datetime(2026, 1, 5, 2, 5)
    assert email_templates.format_tanggal_wib(waktu_naive) == "5 Januari 2026, 09.05 WIB"


def test_email_pembayaran_berhasil_memuat_tanggal_dan_logo_tanpa_aktif_sampai() -> None:
    dibayar = datetime(2026, 11, 27, 3, 46, tzinfo=UTC)
    isi = email_templates.email_pembayaran_berhasil(
        nama="Sari",
        nomor_invoice="KRS-7F3A9C21",
        nama_paket="Langganan Pro 1 Bulan",
        nominal=30000,
        dibayar_pada=dibayar,
        tautan_invoice="https://koreksi-in.sulthanfarizan.my.id/invoice/KRS-7F3A9C21",
        frontend_url="https://koreksi-in.sulthanfarizan.my.id/",
    )

    assert isi.subjek == "Pembayaran Koreksi-in berhasil"
    for bagian in (isi.html, isi.teks):
        assert "KRS-7F3A9C21" in bagian
        assert "Langganan Pro 1 Bulan" in bagian
        assert "Rp 30.000" in bagian
        assert "Dibayar pada" in bagian
        assert "27 November 2026, 10.46 WIB" in bagian
        assert "https://koreksi-in.sulthanfarizan.my.id/invoice/KRS-7F3A9C21" in bagian
        assert "Aktif sampai" not in bagian
        assert "Batas pembayaran" not in bagian
        assert "HANYA UNTUK MOCKUP" not in bagian

    assert 'src="https://koreksi-in.sulthanfarizan.my.id/logo-ikon.png"' in isi.html
    assert 'alt="Logo Koreksi-in"' in isi.html


def test_email_pembayaran_kedaluwarsa_memuat_no_pesanan_tanpa_batas_pembayaran() -> None:
    isi = email_templates.email_pembayaran_kedaluwarsa(
        nama="Sari",
        nomor_invoice="KRS-7F3A9C21",
        nama_paket="Langganan Pro 1 Bulan",
        nominal=30000,
        tautan_langganan="https://koreksi-in.sulthanfarizan.my.id/langganan",
        frontend_url="https://koreksi-in.sulthanfarizan.my.id",
    )

    assert isi.subjek == "Pembayaran Koreksi-in kedaluwarsa"
    for bagian in (isi.html, isi.teks):
        assert "No. pesanan" in bagian
        assert "KRS-7F3A9C21" in bagian
        assert "Langganan Pro 1 Bulan" in bagian
        assert "Rp 30.000" in bagian
        assert "https://koreksi-in.sulthanfarizan.my.id/langganan" in bagian
        assert "Batas pembayaran" not in bagian
        assert "Aktif sampai" not in bagian
        assert "HANYA UNTUK MOCKUP" not in bagian

    assert 'src="https://koreksi-in.sulthanfarizan.my.id/logo-ikon.png"' in isi.html
    assert 'alt="Logo Koreksi-in"' in isi.html


def test_email_templates_escape_nama_pada_html() -> None:
    nama_mentah = "Budi & Siti <script>alert(1)</script>"
    dibayar = datetime(2026, 11, 27, 3, 46, tzinfo=UTC)

    berhasil = email_templates.email_pembayaran_berhasil(
        nama=nama_mentah,
        nomor_invoice="KRS-123",
        nama_paket="Langganan Pro 1 Bulan",
        nominal=30000,
        dibayar_pada=dibayar,
        tautan_invoice="http://localhost:5173/invoice/KRS-123",
        frontend_url="http://localhost:5173",
    )
    kedaluwarsa = email_templates.email_pembayaran_kedaluwarsa(
        nama=nama_mentah,
        nomor_invoice="KRS-123",
        nama_paket="Langganan Pro 1 Bulan",
        nominal=30000,
        tautan_langganan="http://localhost:5173/langganan",
        frontend_url="http://localhost:5173",
    )

    for isi in (berhasil, kedaluwarsa):
        assert "<script>" not in isi.html
        assert "Budi & Siti" not in isi.html
        assert "Budi &amp; Siti &lt;script&gt;alert(1)&lt;/script&gt;" in isi.html
        assert nama_mentah in isi.teks


async def test_invoice_milik_sendiri_sukses(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _token_pengajar(client, db_session, email="pemilik@contoh.id")
    pemilik = await _ambil_pengguna(db_session, "pemilik@contoh.id")
    await _buat_transaksi(db_session, pemilik, id_order="KRS-milik-1")

    response = await client.get("/api/langganan/invoice/KRS-milik-1", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["nomor_invoice"] == "KRS-milik-1"
    assert body["nama_pengajar"] == "Pengajar Test"
    assert body["email_pengajar"] == "pemilik@contoh.id"
    assert body["metode_pembayaran"] == "Transfer Bank"
    assert body["paket"] == "Langganan Pro 1 Bulan"
    assert body["nominal"] == 30000


async def test_invoice_milik_pengajar_lain_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _token_pengajar(client, db_session, email="peminta@contoh.id")
    lain = await _buat_pengguna(db_session, nama="Lain", email="lain@contoh.id")
    await _buat_transaksi(db_session, lain, id_order="KRS-milik-lain")

    response = await client.get("/api/langganan/invoice/KRS-milik-lain", headers=headers)

    assert response.status_code == 404
    assert response.json()["kode"] == "INVOICE_TIDAK_DITEMUKAN"


async def test_invoice_belum_lunas_404(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _token_pengajar(client, db_session, email="menunggu@contoh.id")
    pengguna = await _ambil_pengguna(db_session, "menunggu@contoh.id")
    await _buat_transaksi(
        db_session,
        pengguna,
        id_order="KRS-menunggu-1",
        status=StatusTransaksi.MENUNGGU,
        metode_pembayaran=None,
    )

    response = await client.get("/api/langganan/invoice/KRS-menunggu-1", headers=headers)

    assert response.status_code == 404
    assert response.json()["kode"] == "INVOICE_TIDAK_DITEMUKAN"


async def test_invoice_tidak_ada_404(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _token_pengajar(client, db_session, email="kosong@contoh.id")

    response = await client.get("/api/langganan/invoice/KRS-tidak-ada", headers=headers)

    assert response.status_code == 404
    assert response.json()["kode"] == "INVOICE_TIDAK_DITEMUKAN"


async def _ambil_pengguna(db_session: AsyncSession, email: str) -> Pengguna:
    return await db_session.scalar(select(Pengguna).where(Pengguna.email == email))
