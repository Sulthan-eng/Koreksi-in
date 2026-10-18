import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import StatusProses, nilai_enum


class FileJawaban(Base):
    __tablename__ = "File_Jawaban"

    id_file: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_batch: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Batch.id_batch", ondelete="CASCADE"), nullable=False
    )
    nama_peserta_didik: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    status_proses: Mapped[StatusProses] = mapped_column(
        Enum(StatusProses, name="status_proses", values_callable=nilai_enum), nullable=False
    )
    pesan_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    jumlah_retry: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    diunggah_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
