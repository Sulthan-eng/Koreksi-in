import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import StatusLangganan, nilai_enum


class Pengguna(Base):
    __tablename__ = "Pengguna"

    id_pengguna: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status_langganan: Mapped[StatusLangganan] = mapped_column(
        Enum(StatusLangganan, name="status_langganan", values_callable=nilai_enum),
        nullable=False,
        server_default=StatusLangganan.FREE.value,
    )
    masa_berlaku_pro: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dibuat_pada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
