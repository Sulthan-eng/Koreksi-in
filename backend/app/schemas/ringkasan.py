from pydantic import BaseModel


class RingkasanResponse(BaseModel):
    total_batch: int
    peserta_didik_dikoreksi: int
    sisa_slot_batch_aktif: int | None
    sisa_slot_jawaban_per_batch: int | None
