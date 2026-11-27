import re
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.models.enums import Peran, StatusLangganan

POLA_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


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
        if POLA_EMAIL.match(value) is None:
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
    email: str
    status_langganan: StatusLangganan
    masa_berlaku_pro: datetime | None = None
    peran: Peran
    dibuat_pada: datetime


class LupaPasswordRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def _validasi_email(cls, value: str) -> str:
        stripped = _strip_dan_tolak_kosong(value)
        if POLA_EMAIL.match(stripped) is None:
            raise ValueError("format email tidak valid")
        return stripped


class LupaPasswordResponse(BaseModel):
    pesan: str = "Tautan Atur Ulang Password Telah Dikirim"


class AturUlangPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    password_baru: str = Field(min_length=1)

    @field_validator("token")
    @classmethod
    def _validasi_token(cls, value: str) -> str:
        return _strip_dan_tolak_kosong(value)


class UbahProfilRequest(BaseModel):
    nama: str = Field(min_length=1, max_length=100)

    @field_validator("nama")
    @classmethod
    def _validasi_nama(cls, value: str) -> str:
        return _strip_dan_tolak_kosong(value)


class GantiPasswordRequest(BaseModel):
    password_lama: str = Field(min_length=1)
    password_baru: str = Field(min_length=1)
    konfirmasi_password_baru: str = Field(min_length=1)

    @field_validator("konfirmasi_password_baru")
    @classmethod
    def _validasi_konfirmasi(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data.get("password_baru"):
            raise ValueError("konfirmasi password baru tidak cocok")
        return value
