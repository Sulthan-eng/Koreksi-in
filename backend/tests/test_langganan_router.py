import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import PaketLangganan, Peran, StatusTransaksi
from app.models.pengguna import Pengguna
from app.models.transaksi_pembayaran import TransaksiPembayaran
from app.services import midtrans


async def _buat_pengguna(
    db_session: AsyncSession,
    *,
    nama: str,
    email: str,
    password: str = "rahasia123",
    peran: Peran = Peran.PENGAJAR,
    dinonaktifkan_pada=None,
) -> Pengguna:
    pengguna = Pengguna(
        nama=nama,
        email=email,
        password_hash=await hash_password(password),
        peran=peran,
        dinonaktifkan_pada=dinonaktifkan_pada,
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


async def test_buat_transaksi_sukses(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    headers = await _token_pengajar(client, db_session)
    monkeypatch.setattr(
        midtrans, "buat_transaksi_snap", AsyncMock(return_value="https://sandbox/pay/abc")
    )

    response = await client.post(
        "/api/langganan/transaksi", json={"paket": "pro_1_bulan"}, headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["redirect_url"] == "https://sandbox/pay/abc"

    transaksi = await db_session.scalar(
        select(TransaksiPembayaran).where(
            TransaksiPembayaran.id_transaksi == uuid.UUID(body["id_transaksi"])
        )
    )
    assert transaksi is not None
    assert transaksi.status == StatusTransaksi.MENUNGGU
    assert transaksi.paket == PaketLangganan.PRO_1_BULAN
    assert transaksi.nominal == 30000


async def test_buat_transaksi_gagal_snap_tidak_membuat_baris(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    headers = await _token_pengajar(client, db_session)
    monkeypatch.setattr(
        midtrans,
        "buat_transaksi_snap",
        AsyncMock(side_effect=midtrans.MidtransGagalDibuat()),
    )

    response = await client.post(
        "/api/langganan/transaksi", json={"paket": "pro_3_bulan"}, headers=headers
    )

    assert response.status_code == 500
    assert response.json()["kode"] == "TRANSAKSI_GAGAL_DIBUAT"
    sisa = await db_session.scalars(select(TransaksiPembayaran))
    assert list(sisa) == []


async def test_buat_transaksi_gagal_mencatat_saat_id_order_bentrok(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    headers = await _token_pengajar(client, db_session)
    id_tetap = uuid.UUID("11111111-1111-1111-1111-111111111111")

    class _UuidTetap:
        hex = id_tetap.hex

    monkeypatch.setattr("app.services.transaksi.uuid.uuid4", lambda: _UuidTetap())
    pengguna = await db_session.scalar(
        select(Pengguna).where(Pengguna.email == "pengajar@contoh.id")
    )
    db_session.add(
        TransaksiPembayaran(
            id_pengguna=pengguna.id_pengguna,
            id_order=f"KRS-{id_tetap.hex}",
            paket=PaketLangganan.PRO_1_BULAN,
            nominal=30000,
            status=StatusTransaksi.MENUNGGU,
            diperbarui_pada=pengguna.dibuat_pada,
        )
    )
    await db_session.commit()
    monkeypatch.setattr(
        midtrans, "buat_transaksi_snap", AsyncMock(return_value="https://sandbox/pay/abc")
    )

    response = await client.post(
        "/api/langganan/transaksi", json={"paket": "pro_1_bulan"}, headers=headers
    )

    assert response.status_code == 500
    assert response.json()["kode"] == "GAGAL_MENCATAT_TRANSAKSI"


async def test_buat_transaksi_tanpa_token_401(client: AsyncClient) -> None:
    response = await client.post("/api/langganan/transaksi", json={"paket": "pro_1_bulan"})

    assert response.status_code == 401


async def test_buat_transaksi_akun_nonaktif_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Login dulu selagi aktif (login dengan akun nonaktif ditolak lebih awal oleh
    # /auth/masuk), lalu nonaktifkan -- mencerminkan deaktivasi Admin pada sesi
    # yang sedang berjalan (FR26): pengguna_saat_ini yang menolaknya, bukan login.
    headers = await _token_pengajar(client, db_session, email="akan-nonaktif@contoh.id")
    pengguna = await db_session.scalar(
        select(Pengguna).where(Pengguna.email == "akan-nonaktif@contoh.id")
    )
    pengguna.dinonaktifkan_pada = datetime.now(UTC)
    await db_session.commit()

    response = await client.post(
        "/api/langganan/transaksi", json={"paket": "pro_1_bulan"}, headers=headers
    )

    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_daftar_transaksi_hanya_milik_sendiri(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _token_pengajar(client, db_session, email="pemilik@contoh.id")
    pemilik = await db_session.scalar(select(Pengguna).where(Pengguna.email == "pemilik@contoh.id"))
    lain = await _buat_pengguna(db_session, nama="Lain", email="lain@contoh.id")

    db_session.add_all(
        [
            TransaksiPembayaran(
                id_pengguna=pemilik.id_pengguna,
                id_order="KRS-milik-1",
                paket=PaketLangganan.PRO_1_BULAN,
                nominal=30000,
                status=StatusTransaksi.MENUNGGU,
                diperbarui_pada=pemilik.dibuat_pada,
            ),
            TransaksiPembayaran(
                id_pengguna=lain.id_pengguna,
                id_order="KRS-lain-1",
                paket=PaketLangganan.PRO_3_BULAN,
                nominal=80000,
                status=StatusTransaksi.MENUNGGU,
                diperbarui_pada=lain.dibuat_pada,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/langganan/transaksi", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["paket"] == "pro_1_bulan"
    assert body[0]["nominal"] == 30000
