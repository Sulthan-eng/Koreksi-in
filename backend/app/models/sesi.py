import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Sesi(Base):
    __tablename__ = "Sesi"

    id_sesi: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_pengguna: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Pengguna.id_pengguna", ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    terakhir_dipakai_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kedaluwarsa_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dicabut_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
