import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import PaketLangganan, Peran, StatusLangganan, StatusTransaksi
from app.models.pengguna import Pengguna
from app.models.transaksi_pembayaran import TransaksiPembayaran

_URL = "/api/midtrans/notifikasi"


def _signature(order_id: str, status_code: str, gross_amount: str) -> str:
    mentah = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    return hashlib.sha512(mentah.encode("utf-8")).hexdigest()


def _notifikasi(
    order_id: str,
    transaction_status: str,
    gross_amount: str = "30000.00",
    status_code: str = "200",
    fraud_status: str | None = "accept",
) -> dict:
    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "transaction_status": transaction_status,
        "signature_key": _signature(order_id, status_code, gross_amount),
    }
    if fraud_status is not None:
        payload["fraud_status"] = fraud_status
    return payload


async def _buat_pengguna_dan_transaksi(
    db_session: AsyncSession,
    *,
    email: str,
    order_id: str,
    nominal: int = 30000,
    paket: PaketLangganan = PaketLangganan.PRO_1_BULAN,
    status_langganan: StatusLangganan = StatusLangganan.FREE,
    masa_berlaku_pro=None,
) -> tuple[Pengguna, TransaksiPembayaran]:
    pengguna = Pengguna(
        nama="Pengajar Test",
        email=email,
        password_hash="x",
        peran=Peran.PENGAJAR,
        status_langganan=status_langganan,
        masa_berlaku_pro=masa_berlaku_pro,
    )
    db_session.add(pengguna)
    await db_session.commit()
    await db_session.refresh(pengguna)

    transaksi = TransaksiPembayaran(
        id_pengguna=pengguna.id_pengguna,
        id_order=order_id,
        paket=paket,
        nominal=nominal,
        status=StatusTransaksi.MENUNGGU,
        diperbarui_pada=datetime.now(UTC),
    )
    db_session.add(transaksi)
    await db_session.commit()
    await db_session.refresh(transaksi)
    return pengguna, transaksi


async def test_signature_valid_settlement_mengaktifkan_pro(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="sukses@contoh.id", order_id=order_id
    )

    response = await client.post(_URL, json=_notifikasi(order_id, "settlement"))

    assert response.status_code == 200
    await db_session.refresh(transaksi)
    await db_session.refresh(pengguna)
    assert transaksi.status == StatusTransaksi.BERHASIL
    assert pengguna.status_langganan == StatusLangganan.PRO
    assert pengguna.masa_berlaku_pro is not None


async def test_signature_valid_perpanjangan_pro_aktif(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    masa_berlaku_lama = datetime.now(UTC) + timedelta(days=10)
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session,
        email="perpanjang@contoh.id",
        order_id=order_id,
        paket=PaketLangganan.PRO_3_BULAN,
        nominal=80000,
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=masa_berlaku_lama,
    )

    response = await client.post(
        _URL, json=_notifikasi(order_id, "settlement", gross_amount="80000.00")
    )

    assert response.status_code == 200
    await db_session.refresh(pengguna)
    assert pengguna.masa_berlaku_pro == masa_berlaku_lama + timedelta(days=90)


async def test_signature_palsu_401_dan_tidak_mengubah_apa_pun(
    client: AsyncClient, db_session: AsyncSession, caplog
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="palsu@contoh.id", order_id=order_id
    )
    payload = _notifikasi(order_id, "settlement")
    payload["signature_key"] = "signature-tidak-valid"

    response = await client.post(_URL, json=payload)

    assert response.status_code == 401
    assert response.json()["kode"] == "SIGNATURE_TIDAK_VALID"
    await db_session.refresh(transaksi)
    await db_session.refresh(pengguna)
    assert transaksi.status == StatusTransaksi.MENUNGGU
    assert pengguna.status_langganan == StatusLangganan.FREE

    pesan_warning = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert any(order_id in p for p in pesan_warning)
    for p in pesan_warning:
        assert "signature-tidak-valid" not in p
        assert "gross_amount" not in p


async def test_body_bukan_json_ditolak_400(client: AsyncClient) -> None:
    response = await client.post(
        _URL, content=b"bukan json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert response.json()["kode"] == "NOTIFIKASI_TIDAK_VALID"


async def test_field_wajib_hilang_ditolak_400(client: AsyncClient) -> None:
    response = await client.post(_URL, json={"order_id": "KRS-abc", "status_code": "200"})

    assert response.status_code == 400
    assert response.json()["kode"] == "NOTIFIKASI_TIDAK_VALID"


async def test_notifikasi_duplikat_tidak_memperpanjang_dua_kali(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="duplikat@contoh.id", order_id=order_id
    )
    notifikasi = _notifikasi(order_id, "settlement")

    pertama = await client.post(_URL, json=notifikasi)
    await db_session.refresh(pengguna)
    masa_berlaku_setelah_pertama = pengguna.masa_berlaku_pro

    kedua = await client.post(_URL, json=notifikasi)
    await db_session.refresh(pengguna)

    assert pertama.status_code == 200
    assert kedua.status_code == 200
    assert pengguna.masa_berlaku_pro == masa_berlaku_setelah_pertama


async def test_order_id_tidak_dikenal_404(client: AsyncClient) -> None:
    order_id = "KRS-tidak-ada"
    response = await client.post(_URL, json=_notifikasi(order_id, "settlement"))

    assert response.status_code == 404
    assert response.json()["kode"] == "TRANSAKSI_TIDAK_DITEMUKAN"


async def test_gross_amount_tidak_cocok_tetap_menunggu(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="nominal-salah@contoh.id", order_id=order_id, nominal=30000
    )

    response = await client.post(
        _URL, json=_notifikasi(order_id, "settlement", gross_amount="999999.00")
    )

    assert response.status_code == 200
    await db_session.refresh(transaksi)
    assert transaksi.status == StatusTransaksi.MENUNGGU


async def test_mapping_deny_cancel_failure_jadi_gagal(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    for transaction_status in ("deny", "cancel", "failure"):
        order_id = f"KRS-{uuid.uuid4().hex}"
        _, transaksi = await _buat_pengguna_dan_transaksi(
            db_session, email=f"{transaction_status}@contoh.id", order_id=order_id
        )

        response = await client.post(
            _URL, json=_notifikasi(order_id, transaction_status, fraud_status=None)
        )

        assert response.status_code == 200
        await db_session.refresh(transaksi)
        assert transaksi.status == StatusTransaksi.GAGAL, transaction_status


async def test_mapping_expire_jadi_kedaluwarsa(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    _, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="expire@contoh.id", order_id=order_id
    )

    response = await client.post(_URL, json=_notifikasi(order_id, "expire", fraud_status=None))

    assert response.status_code == 200
    await db_session.refresh(transaksi)
    assert transaksi.status == StatusTransaksi.KEDALUWARSA


async def test_mapping_pending_tetap_menunggu(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    _, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="pending@contoh.id", order_id=order_id
    )

    response = await client.post(_URL, json=_notifikasi(order_id, "pending", fraud_status=None))

    assert response.status_code == 200
    await db_session.refresh(transaksi)
    assert transaksi.status == StatusTransaksi.MENUNGGU


async def test_mapping_capture_challenge_tetap_menunggu(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    order_id = f"KRS-{uuid.uuid4().hex}"
    pengguna, transaksi = await _buat_pengguna_dan_transaksi(
        db_session, email="challenge@contoh.id", order_id=order_id
    )

    response = await client.post(
        _URL, json=_notifikasi(order_id, "capture", fraud_status="challenge")
    )

    assert response.status_code == 200
    await db_session.refresh(transaksi)
    await db_session.refresh(pengguna)
    assert transaksi.status == StatusTransaksi.MENUNGGU
    assert pengguna.status_langganan == StatusLangganan.FREE
