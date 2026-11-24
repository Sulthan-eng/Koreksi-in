import uuid
from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PemakaianGemini(Base):
    __tablename__ = "Pemakaian_Gemini"
    __table_args__ = (
        UniqueConstraint("tanggal", "model", name="uq_pemakaian_gemini_tanggal_model"),
    )

    id_pemakaian_gemini: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tanggal: Mapped[date] = mapped_column(Date, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    jumlah_panggilan: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
