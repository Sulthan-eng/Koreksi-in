import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import StatusLangganan


class StatusAkunFilter(enum.Enum):
    AKTIF = "aktif"
    NONAKTIF = "nonaktif"


class AkunPengajarResponse(BaseModel):
    id_pengguna: uuid.UUID
    nama: str
    email: str
    status_langganan: StatusLangganan
    masa_berlaku_pro: datetime | None
    dinonaktifkan_pada: datetime | None
    dibuat_pada: datetime
    jumlah_batch: int


class UbahLanggananRequest(BaseModel):
    status_langganan: StatusLangganan
    # Validasi tipe, format, dan batas tanggal Pro dilakukan di service agar
    # masukan kosong atau tidak valid mengembalikan 400 MASA_BERLAKU_TIDAK_VALID.
    masa_berlaku_pro: Any = None


class KuotaResponse(BaseModel):
    terpakai: int
    batas: int
    nama_model: str


class RingkasanDashboardResponse(BaseModel):
    jumlah_akun_pengajar: int
    jumlah_akun_free: int
    jumlah_akun_pro: int
    jumlah_batch: int
    jumlah_file_diproses: int
    jumlah_file_selesai: int
    jumlah_file_gagal: int
    kuota: KuotaResponse
