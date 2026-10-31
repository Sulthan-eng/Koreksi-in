import re
import uuid

from pydantic import BaseModel, Field, field_validator

_POLA_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


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

    @field_validator("email")
    @classmethod
    def _validasi_format_email(cls, value: str) -> str:
        # Berjalan setelah trim (urutan definisi validator), jadi pola sengaja tanpa spasi tepi.
        if _POLA_EMAIL.match(value) is None:
            raise ValueError("format email tidak valid")
        return value


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
