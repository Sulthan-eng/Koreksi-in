import uuid

from pydantic import BaseModel

from app.models.enums import StatusProses


class FileJawabanResponse(BaseModel):
    id_file: uuid.UUID
    nama_peserta_didik: str
    status_proses: StatusProses
    pesan_error: str | None
