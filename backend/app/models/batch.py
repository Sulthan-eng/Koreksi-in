import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import StatusBatch, nilai_enum


class Batch(Base):
    __tablename__ = "Batch"

    id_batch: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_pengguna: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Pengguna.id_pengguna", ondelete="CASCADE"), nullable=False
    )
    nama_batch: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[StatusBatch] = mapped_column(
        Enum(StatusBatch, name="status_batch", values_callable=nilai_enum),
        nullable=False,
        server_default=StatusBatch.AKTIF.value,
    )
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
