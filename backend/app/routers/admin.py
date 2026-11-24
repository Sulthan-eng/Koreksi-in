import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import admin_saat_ini
from app.models.enums import StatusLangganan
from app.models.pengguna import Pengguna
from app.schemas.admin import (
    AkunPengajarResponse,
    KuotaResponse,
    RingkasanDashboardResponse,
    StatusAkunFilter,
    UbahLanggananRequest,
)
from app.services import admin as admin_service

router = APIRouter(prefix="/admin")


def _akun_response(item: admin_service.AkunPengajarItem) -> AkunPengajarResponse:
    return AkunPengajarResponse(
        id_pengguna=item.id_pengguna,
        nama=item.nama,
        email=item.email,
        status_langganan=item.status_langganan,
        masa_berlaku_pro=item.masa_berlaku_pro,
        dinonaktifkan_pada=item.dinonaktifkan_pada,
        dibuat_pada=item.dibuat_pada,
        jumlah_batch=item.jumlah_batch,
    )


def _ringkasan_response(
    item: admin_service.RingkasanDashboard,
) -> RingkasanDashboardResponse:
    return RingkasanDashboardResponse(
        jumlah_akun_pengajar=item.jumlah_akun_pengajar,
        jumlah_akun_free=item.jumlah_akun_free,
        jumlah_akun_pro=item.jumlah_akun_pro,
        jumlah_batch=item.jumlah_batch,
        jumlah_file_diproses=item.jumlah_file_diproses,
        jumlah_file_selesai=item.jumlah_file_selesai,
        jumlah_file_gagal=item.jumlah_file_gagal,
        kuota=KuotaResponse(
            terpakai=item.kuota_terpakai,
            batas=item.kuota_batas,
            nama_model=item.nama_model,
        ),
    )


@router.get("/ringkasan", response_model=RingkasanDashboardResponse)
async def ringkasan_dashboard(
    _: Pengguna = Depends(admin_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> RingkasanDashboardResponse:
    item = await admin_service.ambil_ringkasan_dashboard(db)
    return _ringkasan_response(item)


@router.get("/akun-pengajar", response_model=list[AkunPengajarResponse])
async def daftar_akun_pengajar(
    cari: str | None = None,
    status_langganan: StatusLangganan | None = None,
    status_akun: StatusAkunFilter | None = None,
    _: Pengguna = Depends(admin_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> list[AkunPengajarResponse]:
    daftar = await admin_service.daftar_akun_pengajar(
        db, cari=cari, status_langganan=status_langganan, status_akun=status_akun
    )
    return [_akun_response(item) for item in daftar]


@router.patch("/akun-pengajar/{id_pengguna}/langganan", response_model=AkunPengajarResponse)
async def ubah_langganan_pengajar(
    id_pengguna: uuid.UUID,
    body: UbahLanggananRequest,
    _: Pengguna = Depends(admin_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> AkunPengajarResponse:
    item = await admin_service.ubah_langganan_pengajar(
        db, id_pengguna, body.status_langganan, body.masa_berlaku_pro
    )
    return _akun_response(item)


@router.post("/akun-pengajar/{id_pengguna}/nonaktifkan", response_model=AkunPengajarResponse)
async def nonaktifkan_pengajar(
    id_pengguna: uuid.UUID,
    _: Pengguna = Depends(admin_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> AkunPengajarResponse:
    item = await admin_service.nonaktifkan_pengajar(db, id_pengguna)
    return _akun_response(item)


@router.post("/akun-pengajar/{id_pengguna}/aktifkan", response_model=AkunPengajarResponse)
async def aktifkan_pengajar(
    id_pengguna: uuid.UUID,
    _: Pengguna = Depends(admin_saat_ini),
    db: AsyncSession = Depends(get_db),
) -> AkunPengajarResponse:
    item = await admin_service.aktifkan_pengajar(db, id_pengguna)
    return _akun_response(item)
