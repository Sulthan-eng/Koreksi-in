import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import pengguna_saat_ini
from app.models.pengguna import Pengguna
from app.schemas.batch import BatchResponse, BuatBatchRequest
from app.schemas.soal import SoalResponse, TambahSoalRequest
from app.services import batch as batch_service
from app.services import soal as soal_service

router = APIRouter(prefix="/batch")


def _batch_response(batch) -> BatchResponse:
    return BatchResponse(
        id_batch=batch.id_batch,
        nama_batch=batch.nama_batch,
        status=batch.status,
        dibuat_pada=batch.dibuat_pada,
    )


def _soal_response(soal) -> SoalResponse:
    return SoalResponse(
        id_soal=soal.id_soal, no_soal=soal.no_soal, kunci_jawaban=soal.kunci_jawaban
    )


@router.get("", response_model=list[BatchResponse])
async def daftar_batch(
    pengguna: Pengguna = Depends(pengguna_saat_ini), db: AsyncSession = Depends(get_db)
) -> list[BatchResponse]:
    batch_list = await batch_service.daftar_batch(db, pengguna)
    return [_batch_response(batch) for batch in batch_list]


@router.post("", response_model=BatchResponse, status_code=201)
async def buat_batch(
    body: BuatBatchRequest,
    pengguna: Pengguna = Depends(pengguna_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    batch = await batch_service.buat_batch(db, pengguna, body.nama_batch)
    return _batch_response(batch)


@router.get("/{id_batch}", response_model=BatchResponse)
async def ambil_batch(
    id_batch: uuid.UUID,
    pengguna: Pengguna = Depends(pengguna_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> BatchResponse:
    batch = await batch_service.ambil_batch(db, pengguna, id_batch)
    return _batch_response(batch)


@router.get("/{id_batch}/soal", response_model=list[SoalResponse])
async def daftar_soal(
    id_batch: uuid.UUID,
    pengguna: Pengguna = Depends(pengguna_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> list[SoalResponse]:
    soal_list = await soal_service.daftar_soal(db, pengguna, id_batch)
    return [_soal_response(soal) for soal in soal_list]


@router.post("/{id_batch}/soal", response_model=SoalResponse, status_code=201)
async def tambah_soal(
    id_batch: uuid.UUID,
    body: TambahSoalRequest,
    pengguna: Pengguna = Depends(pengguna_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> SoalResponse:
    soal = await soal_service.tambah_soal(db, pengguna, id_batch, body.kunci_jawaban)
    return _soal_response(soal)
