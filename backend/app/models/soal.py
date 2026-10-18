import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Soal(Base):
    __tablename__ = "Soal"
    __table_args__ = (UniqueConstraint("id_batch", "no_soal", name="uq_soal_id_batch_no_soal"),)

    id_soal: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    id_batch: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("Batch.id_batch", ondelete="CASCADE"), nullable=False
    )
    no_soal: Mapped[int] = mapped_column(Integer, nullable=False)
    kunci_jawaban: Mapped[str] = mapped_column(Text, nullable=False)
