from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import transaksi as transaksi_service

router = APIRouter(prefix="/midtrans")


@router.post("/notifikasi", status_code=200)
async def notifikasi(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        payload = await request.json()
    except ValueError:
        raise transaksi_service.NOTIFIKASI_TIDAK_VALID from None

    await transaksi_service.proses_notifikasi(db, payload)

    return {"status": "ok"}
