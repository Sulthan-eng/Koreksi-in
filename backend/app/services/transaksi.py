"""Orkestrasi transaksi pembayaran Pro (FR19/FR20): membuat transaksi Snap lewat
app/services/midtrans.py, mencatatnya, dan memproses notifikasi webhook."""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.enums import PaketLangganan, StatusLangganan, StatusTransaksi
from app.models.pengguna import Pengguna
from app.models.transaksi_pembayaran import TransaksiPembayaran
from app.services import midtrans
from app.services.langganan import HARGA_PAKET, hitung_masa_berlaku_baru

logger = logging.getLogger(__name__)

_NAMA_PAKET: dict[PaketLangganan, str] = {
    PaketLangganan.PRO_1_BULAN: "Langganan Pro 1 Bulan",
    PaketLangganan.PRO_3_BULAN: "Langganan Pro 3 Bulan",
}

_FIELD_WAJIB = ("order_id", "status_code", "gross_amount", "signature_key")

TRANSAKSI_GAGAL_DIBUAT = AppError(
    kode="TRANSAKSI_GAGAL_DIBUAT",
    pesan="Transaksi gagal dibuat, silakan coba lagi.",
    status_code=500,
)
GAGAL_MENCATAT_TRANSAKSI = AppError(
    kode="GAGAL_MENCATAT_TRANSAKSI",
    pesan="Gagal mencatat transaksi, silakan coba lagi.",
    status_code=500,
)
NOTIFIKASI_TIDAK_VALID = AppError(
    kode="NOTIFIKASI_TIDAK_VALID", pesan="Notifikasi tidak valid.", status_code=400
)
SIGNATURE_TIDAK_VALID = AppError(
    kode="SIGNATURE_TIDAK_VALID", pesan="Signature tidak valid.", status_code=401
)
TRANSAKSI_TIDAK_DITEMUKAN = AppError(
    kode="TRANSAKSI_TIDAK_DITEMUKAN", pesan="Transaksi tidak ditemukan.", status_code=404
)


async def buat_transaksi(
    db: AsyncSession, pengguna: Pengguna, paket: PaketLangganan
) -> tuple[TransaksiPembayaran, str]:
    """Buat transaksi Snap di Midtrans lalu catat lokal. Jika pembuatan Snap
    gagal, tidak ada baris yang dibuat sama sekali. Jika Snap sukses tapi
    pencatatan lokal gagal, transaksi tetap ada di sisi Midtrans tanpa baris
    lokal -- risiko diterima, lihat pesan error yang berbeda untuk dua
    kegagalan ini."""
    id_order = f"KRS-{uuid.uuid4().hex}"
    nominal = HARGA_PAKET[paket]

    try:
        redirect_url = await midtrans.buat_transaksi_snap(id_order, nominal, _NAMA_PAKET[paket])
    except midtrans.MidtransGagalDibuat as exc:
        raise TRANSAKSI_GAGAL_DIBUAT from exc

    sekarang = datetime.now(UTC)
    transaksi = TransaksiPembayaran(
        id_pengguna=pengguna.id_pengguna,
        id_order=id_order,
        paket=paket,
        nominal=nominal,
        status=StatusTransaksi.MENUNGGU,
        diperbarui_pada=sekarang,
    )
    db.add(transaksi)
    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise GAGAL_MENCATAT_TRANSAKSI from exc
    await db.refresh(transaksi)

    return transaksi, redirect_url


async def daftar_transaksi(db: AsyncSession, pengguna: Pengguna) -> list[TransaksiPembayaran]:
    hasil = await db.scalars(
        select(TransaksiPembayaran)
        .where(TransaksiPembayaran.id_pengguna == pengguna.id_pengguna)
        .order_by(TransaksiPembayaran.dibuat_pada.desc())
    )
    return list(hasil)


def _petakan_status(transaction_status: str, fraud_status: str | None) -> StatusTransaksi | None:
    """None berarti tidak ada transisi (status tetap, no-op). Lihat SPEC
    bagian 9 (F-LANGGANAN) untuk pemetaan lengkap."""
    if transaction_status in ("capture", "settlement"):
        if fraud_status == "challenge":
            return None
        if fraud_status == "deny":
            return StatusTransaksi.GAGAL
        return StatusTransaksi.BERHASIL
    if transaction_status in ("deny", "cancel", "failure"):
        return StatusTransaksi.GAGAL
    if transaction_status == "expire":
        return StatusTransaksi.KEDALUWARSA
    # "pending", "refund", "partial_refund", "authorize", atau nilai tidak
    # dikenal: di luar cakupan FR19/FR20 atau belum final, tidak mengubah apa pun.
    return None


def _parse_gross_amount(nilai: str) -> int | None:
    try:
        return int(Decimal(nilai))
    except (InvalidOperation, ValueError):
        return None


async def proses_notifikasi(db: AsyncSession, payload: object) -> None:
    if not isinstance(payload, dict) or any(
        not isinstance(payload.get(field), str) for field in _FIELD_WAJIB
    ):
        raise NOTIFIKASI_TIDAK_VALID

    order_id: str = payload["order_id"]
    status_code: str = payload["status_code"]
    gross_amount: str = payload["gross_amount"]
    signature_key: str = payload["signature_key"]

    if not midtrans.validasi_signature(order_id, status_code, gross_amount, signature_key):
        logger.warning("midtrans_signature_tidak_valid order_id=%s", order_id)
        raise SIGNATURE_TIDAK_VALID

    transaksi = await db.scalar(
        select(TransaksiPembayaran)
        .where(TransaksiPembayaran.id_order == order_id)
        .with_for_update()
    )
    if transaksi is None:
        raise TRANSAKSI_TIDAK_DITEMUKAN

    if transaksi.status in (StatusTransaksi.BERHASIL, StatusTransaksi.KEDALUWARSA):
        return

    nominal_payload = _parse_gross_amount(gross_amount)
    if nominal_payload != transaksi.nominal:
        logger.warning("midtrans_nominal_tidak_cocok order_id=%s", order_id)
        return

    status_baru = _petakan_status(
        payload.get("transaction_status", ""), payload.get("fraud_status")
    )
    if status_baru is None:
        return

    if transaksi.status == StatusTransaksi.GAGAL and status_baru != StatusTransaksi.BERHASIL:
        # Transaksi gagal hanya bisa pulih lewat notifikasi sukses: kartu
        # pertama ditolak, pembayar mencoba kartu lain di order yang sama.
        return

    sekarang = datetime.now(UTC)
    transaksi.status = status_baru
    transaksi.diperbarui_pada = sekarang

    if status_baru == StatusTransaksi.BERHASIL:
        pengguna = await db.scalar(
            select(Pengguna).where(Pengguna.id_pengguna == transaksi.id_pengguna).with_for_update()
        )
        pengguna.status_langganan = StatusLangganan.PRO
        pengguna.masa_berlaku_pro = hitung_masa_berlaku_baru(pengguna, transaksi.paket, sekarang)

    await db.commit()
