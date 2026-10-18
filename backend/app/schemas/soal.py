import uuid

from pydantic import BaseModel


class TambahSoalRequest(BaseModel):
    kunci_jawaban: str


class SoalResponse(BaseModel):
    id_soal: uuid.UUID
    no_soal: int
    kunci_jawaban: str
