import uuid

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import Kategori, nilai_enum


class HasilKoreksi(Base):
    __tablename__ = "Hasil_Koreksi"
    __table_args__ = (
        UniqueConstraint("id_file", "id_soal", name="uq_hasil_koreksi_id_file_id_soal"),
        CheckConstraint(
            "skor_sistem IS NULL OR (skor_sistem >= 0 AND skor_sistem <= 100)",
            name="ck_hasil_koreksi_skor_sistem_range",
        ),
    )

    id_koreksi: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_file: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("File_Jawaban.id_file", ondelete="CASCADE"), nullable=False
    )
    id_soal: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Soal.id_soal", ondelete="CASCADE"), nullable=False
    )
    teks_ocr: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    skor_sistem: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kategori: Mapped[Kategori | None] = mapped_column(
        Enum(Kategori, name="kategori", values_callable=nilai_enum), nullable=True
    )
    skor_revisi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skor_hitung_ulang: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
