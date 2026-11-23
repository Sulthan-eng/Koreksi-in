"""Satu-satunya modul yang menghubungi API Midtrans.

Memuat: pembuatan transaksi Snap (tanpa retry otomatis -- retry berisiko
membuat dua transaksi Snap untuk satu id_order yang sama bila permintaan
pertama sebenarnya sukses tapi responsnya hilang) dan validasi signature
notifikasi webhook.
"""

import hashlib
import hmac
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SNAP_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"
_TIMEOUT_DETIK = 15.0


class MidtransGagalDibuat(Exception):
    """Transaksi Snap gagal dibuat (network error, timeout, atau status non-2xx)."""


async def buat_transaksi_snap(id_order: str, nominal: int, nama_paket: str) -> str:
    """Satu-satunya titik yang memanggil Snap create transaction. Mengembalikan
    redirect_url. Tanpa retry -- lihat docstring modul."""
    body = {
        "transaction_details": {"order_id": id_order, "gross_amount": nominal},
        "item_details": [
            {
                "id": id_order,
                "price": nominal,
                "quantity": 1,
                "name": nama_paket,
            }
        ],
        "callbacks": {"finish": f"{settings.FRONTEND_URL}/langganan"},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_DETIK) as client:
            response = await client.post(
                _SNAP_URL,
                json=body,
                auth=(settings.MIDTRANS_SERVER_KEY, ""),
                headers={"Accept": "application/json"},
            )
        response.raise_for_status()
        data = response.json()
        redirect_url = data["redirect_url"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.error("midtrans_snap_gagal id_order=%s tipe=%s", id_order, type(exc).__name__)
        raise MidtransGagalDibuat() from exc

    return redirect_url


def validasi_signature(
    order_id: str, status_code: str, gross_amount: str, signature_key: str
) -> bool:
    """SHA512(order_id + status_code + gross_amount + SignatureSecretKey) harus sama
    dengan signature_key yang dikirim Midtrans. Ketiga field pertama dipakai
    persis seperti diterima (string apa adanya), tanpa parsing ulang jadi
    int/float, karena itulah yang dipakai Midtrans menghitung signature-nya.

    Sejak 28 Oktober 2026 Midtrans menghitung signature_key dengan Signature
    Secret Key, bukan Server Key lagi (lihat docs.midtrans.com/docs/access-keys).
    Server Key tetap dipakai untuk Basic Auth ke Snap API (buat_transaksi_snap)."""
    mentah = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SIGNATURE_SECRET_KEY}"
    hitung = hashlib.sha512(mentah.encode("utf-8")).hexdigest()
    return hmac.compare_digest(hitung, signature_key)
