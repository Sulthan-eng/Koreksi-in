from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import pengguna_saat_ini
from app.models.pengguna import Pengguna
from app.schemas.ringkasan import RingkasanResponse
from app.services import ringkasan as ringkasan_service

router = APIRouter()


@router.get("/ringkasan", response_model=RingkasanResponse)
async def ringkasan(
    pengguna: Pengguna = Depends(pengguna_saat_ini), db: AsyncSession = Depends(get_db)
) -> RingkasanResponse:
    hasil = await ringkasan_service.ambil_ringkasan(db, pengguna)
    return RingkasanResponse(
        total_batch=hasil.total_batch,
        peserta_didik_dikoreksi=hasil.peserta_didik_dikoreksi,
        sisa_slot_batch_aktif=hasil.sisa_slot_batch_aktif,
        sisa_slot_jawaban_per_batch=hasil.sisa_slot_jawaban_per_batch,
    )
