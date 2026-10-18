import uuid

from pydantic import BaseModel, Field, field_validator


def _strip_dan_tolak_kosong(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("tidak boleh kosong setelah di-trim")
    return stripped


class DaftarRequest(BaseModel):
    nama: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)

    @field_validator("nama", "email")
    @classmethod
    def _validasi_nama_email(cls, value: str) -> str:
        return _strip_dan_tolak_kosong(value)


class DaftarResponse(BaseModel):
    id_pengguna: uuid.UUID
    nama: str
    email: str


class MasukRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def _validasi_email(cls, value: str) -> str:
        return _strip_dan_tolak_kosong(value)


class TokenResponse(BaseModel):
    access_token: str


class SayaResponse(BaseModel):
    nama: str
