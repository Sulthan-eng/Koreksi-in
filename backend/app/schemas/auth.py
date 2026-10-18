import uuid

from pydantic import BaseModel, Field


class DaftarRequest(BaseModel):
    nama: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class DaftarResponse(BaseModel):
    id_pengguna: uuid.UUID
    nama: str
    email: str


class MasukRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str


class SayaResponse(BaseModel):
    nama: str
