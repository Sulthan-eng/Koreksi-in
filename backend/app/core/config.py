from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    GEMINI_API_KEY: str
    GEMINI_RPD_LIMIT: int = 450
    MIDTRANS_SERVER_KEY: str
    UPLOAD_DIR: str = ""
    STORAGE_BACKEND: Literal["lokal", "s3"] = "lokal"
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_RECYCLE_SECONDS: int = 300
    # Default "produksi" dipilih agar gagal-aman: origin dev hanya terbuka kalau
    # diminta eksplisit (ENV=dev). Dev sehari-hari tidak terpengaruh karena proxy
    # Vite membuat browser melihat satu origin, jadi CORS tidak terlibat.
    ENV: Literal["dev", "produksi"] = "produksi"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "none", "strict"] = "lax"
    # 10 file x 10 MB (batas per file) + ~5 MB untuk boundary multipart dan field
    # nama_peserta_didik. Tidak menolak unggahan yang sah, hanya memotong request
    # abusif sebelum body dibaca.
    MAX_REQUEST_SIZE_MB: int = 105
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    @model_validator(mode="after")
    def _validasi_cookie(self) -> "Settings":
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SAMESITE=none wajib disertai COOKIE_SECURE=true")
        return self

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
