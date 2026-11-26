from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import pengajar_saat_ini
from app.models.pengguna import Pengguna
from app.schemas.langganan import BuatTransaksiRequest, BuatTransaksiResponse, TransaksiResponse
from app.services import transaksi as transaksi_service

router = APIRouter(prefix="/langganan")


@router.post("/transaksi", response_model=BuatTransaksiResponse, status_code=201)
async def buat_transaksi(
    body: BuatTransaksiRequest,
    pengguna: Pengguna = Depends(pengajar_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> BuatTransaksiResponse:
    transaksi, redirect_url = await transaksi_service.buat_transaksi(db, pengguna, body.paket)
    return BuatTransaksiResponse(id_transaksi=transaksi.id_transaksi, redirect_url=redirect_url)


@router.get("/transaksi", response_model=list[TransaksiResponse])
async def daftar_transaksi(
    pengguna: Pengguna = Depends(pengajar_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> list[TransaksiResponse]:
    daftar = await transaksi_service.daftar_transaksi(db, pengguna)
    return [
        TransaksiResponse(
            id_transaksi=item.id_transaksi,
            id_order=item.id_order,
            paket=item.paket,
            nominal=item.nominal,
            status=item.status,
            dibuat_pada=item.dibuat_pada,
            diperbarui_pada=item.diperbarui_pada,
        )
        for item in daftar
    ]
