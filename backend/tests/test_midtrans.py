import httpx
import pytest

from app.core.config import settings
from app.services import midtrans


class _ResponsPalsu:
    def __init__(self, status_code: int = 200, data: dict | None = None) -> None:
        self.status_code = status_code
        self._data = data if data is not None else {"redirect_url": "https://sandbox/pay/abc"}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "gagal", request=httpx.Request("POST", "https://x"), response=self
            )

    def json(self) -> dict:
        return self._data


class _ClientPalsu:
    def __init__(self, dipanggil: list, respons: _ResponsPalsu | Exception) -> None:
        self._dipanggil = dipanggil
        self._respons = respons

    async def __aenter__(self) -> "_ClientPalsu":
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    async def post(self, url: str, *, json: dict, auth: tuple, headers: dict) -> _ResponsPalsu:
        self._dipanggil.append({"url": url, "json": json, "auth": auth, "headers": headers})
        if isinstance(self._respons, Exception):
            raise self._respons
        return self._respons


def _patch_client(monkeypatch, respons: _ResponsPalsu | Exception) -> list:
    dipanggil: list = []

    def _buat_client(*args, **kwargs):
        return _ClientPalsu(dipanggil, respons)

    monkeypatch.setattr(midtrans.httpx, "AsyncClient", _buat_client)
    return dipanggil


async def test_buat_transaksi_snap_sukses_mengirim_item_details_dan_callbacks(
    monkeypatch,
) -> None:
    dipanggil = _patch_client(monkeypatch, _ResponsPalsu(200, {"redirect_url": "https://url"}))

    hasil = await midtrans.buat_transaksi_snap("KRS-123", 30000, "Langganan Pro 1 Bulan")

    assert hasil == "https://url"
    assert len(dipanggil) == 1
    body = dipanggil[0]["json"]
    assert body["transaction_details"] == {"order_id": "KRS-123", "gross_amount": 30000}
    assert body["item_details"] == [
        {"id": "KRS-123", "price": 30000, "quantity": 1, "name": "Langganan Pro 1 Bulan"}
    ]
    assert body["callbacks"] == {"finish": f"{settings.FRONTEND_URL}/langganan"}
    assert dipanggil[0]["auth"] == (settings.MIDTRANS_SERVER_KEY, "")


async def test_buat_transaksi_snap_gagal_tanpa_retry_satu_percobaan_saja(monkeypatch) -> None:
    dipanggil = _patch_client(monkeypatch, httpx.ConnectTimeout("timeout"))

    with pytest.raises(midtrans.MidtransGagalDibuat):
        await midtrans.buat_transaksi_snap("KRS-456", 30000, "Langganan Pro 1 Bulan")

    assert len(dipanggil) == 1


async def test_buat_transaksi_snap_status_non_2xx_gagal(monkeypatch) -> None:
    _patch_client(monkeypatch, _ResponsPalsu(500, {}))

    with pytest.raises(midtrans.MidtransGagalDibuat):
        await midtrans.buat_transaksi_snap("KRS-789", 30000, "Langganan Pro 1 Bulan")


async def test_buat_transaksi_snap_respons_tanpa_redirect_url_gagal(monkeypatch) -> None:
    _patch_client(monkeypatch, _ResponsPalsu(200, {}))

    with pytest.raises(midtrans.MidtransGagalDibuat):
        await midtrans.buat_transaksi_snap("KRS-000", 30000, "Langganan Pro 1 Bulan")


def test_validasi_signature_benar() -> None:
    import hashlib

    order_id, status_code, gross_amount = "KRS-1", "200", "30000.00"
    mentah = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    signature_key = hashlib.sha512(mentah.encode("utf-8")).hexdigest()

    assert midtrans.validasi_signature(order_id, status_code, gross_amount, signature_key)


def test_validasi_signature_salah() -> None:
    assert not midtrans.validasi_signature("KRS-1", "200", "30000.00", "signature-salah")


def test_validasi_signature_format_gross_amount_harus_persis() -> None:
    import hashlib

    order_id, status_code = "KRS-1", "200"
    mentah_benar = f"{order_id}{status_code}30000.00{settings.MIDTRANS_SERVER_KEY}"
    signature_key = hashlib.sha512(mentah_benar.encode("utf-8")).hexdigest()

    # gross_amount tanpa desimal (format berbeda) harus gagal walau nilainya "sama".
    assert not midtrans.validasi_signature(order_id, status_code, "30000", signature_key)
