import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import PaketLangganan, StatusTransaksi, nilai_enum


class TransaksiPembayaran(Base):
    __tablename__ = "Transaksi_Pembayaran"

    id_transaksi: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_pengguna: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Pengguna.id_pengguna", ondelete="CASCADE"), nullable=False
    )
    id_order: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    paket: Mapped[PaketLangganan] = mapped_column(
        Enum(PaketLangganan, name="paket_langganan", values_callable=nilai_enum),
        nullable=False,
    )
    nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[StatusTransaksi] = mapped_column(
        Enum(StatusTransaksi, name="status_transaksi", values_callable=nilai_enum),
        nullable=False,
        server_default=StatusTransaksi.MENUNGGU.value,
    )
    diperbarui_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metode_pembayaran: Mapped[str | None] = mapped_column(String(50), nullable=True)
