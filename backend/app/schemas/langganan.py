import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PaketLangganan, StatusTransaksi


class BuatTransaksiRequest(BaseModel):
    paket: PaketLangganan


class BuatTransaksiResponse(BaseModel):
    id_transaksi: uuid.UUID
    redirect_url: str


class TransaksiResponse(BaseModel):
    id_transaksi: uuid.UUID
    id_order: str
    paket: PaketLangganan
    nominal: int
    status: StatusTransaksi
    dibuat_pada: datetime
    diperbarui_pada: datetime
