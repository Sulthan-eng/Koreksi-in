from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    GEMINI_API_KEY: str
    GEMINI_RPD_LIMIT: int = 450
    UPLOAD_DIR: str = ""
    STORAGE_BACKEND: Literal["lokal", "s3"] = "lokal"
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    COOKIE_SECURE: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _validasi_storage(self) -> "Settings":
        if self.STORAGE_BACKEND == "lokal" and not self.UPLOAD_DIR:
            raise ValueError("UPLOAD_DIR wajib diisi saat STORAGE_BACKEND=lokal")
        if self.STORAGE_BACKEND == "s3" and not all(
            [
                self.S3_ENDPOINT_URL,
                self.S3_REGION,
                self.S3_BUCKET,
                self.S3_ACCESS_KEY_ID,
                self.S3_SECRET_ACCESS_KEY,
            ]
        ):
            raise ValueError("Konfigurasi S3 tidak lengkap untuk STORAGE_BACKEND=s3")
        return self


settings = Settings()
