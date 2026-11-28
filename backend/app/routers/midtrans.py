from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.enums import StatusTransaksi
from app.services import email as email_service
from app.services import transaksi as transaksi_service

router = APIRouter(prefix="/midtrans")


@router.post("/notifikasi", status_code=200)
async def notifikasi(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        payload = await request.json()
    except ValueError:
        raise transaksi_service.NOTIFIKASI_TIDAK_VALID from None

    hasil = await transaksi_service.proses_notifikasi(db, payload)

    if hasil.status_baru == StatusTransaksi.BERHASIL:
        background_tasks.add_task(
            email_service.kirim_email_pembayaran_berhasil,
            hasil.pengguna.email,
            hasil.pengguna.nama,
            hasil.transaksi.id_order,
            transaksi_service.NAMA_PAKET[hasil.transaksi.paket],
            hasil.transaksi.nominal,
            hasil.transaksi.diperbarui_pada,
        )
    elif hasil.status_baru == StatusTransaksi.KEDALUWARSA:
        background_tasks.add_task(
            email_service.kirim_email_pembayaran_kedaluwarsa,
            hasil.pengguna.email,
            hasil.pengguna.nama,
            hasil.transaksi.id_order,
            transaksi_service.NAMA_PAKET[hasil.transaksi.paket],
            hasil.transaksi.nominal,
        )

    return {"status": "ok"}
