import pytest
from pydantic import ValidationError

from app.core.config import Settings

_DASAR = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "SECRET_KEY": "rahasia",
    "GEMINI_API_KEY": "kunci",
}


def test_storage_lokal_wajib_upload_dir():
    with pytest.raises(ValidationError):
        Settings(**_DASAR, STORAGE_BACKEND="lokal", UPLOAD_DIR="")


def test_storage_lokal_dengan_upload_dir_sukses():
    pengaturan = Settings(**_DASAR, STORAGE_BACKEND="lokal", UPLOAD_DIR="/tmp/unggahan")
    assert pengaturan.UPLOAD_DIR == "/tmp/unggahan"


def test_storage_s3_lengkap_sukses_tanpa_upload_dir():
    pengaturan = Settings(
        **_DASAR,
        STORAGE_BACKEND="s3",
        UPLOAD_DIR="",
        S3_ENDPOINT_URL="https://contoh.supabase.co/storage/v1/s3",
        S3_REGION="ap-southeast-1",
        S3_BUCKET="jawaban",
        S3_ACCESS_KEY_ID="kunci",
        S3_SECRET_ACCESS_KEY="rahasia",
    )
    assert pengaturan.UPLOAD_DIR == ""


def test_storage_s3_tidak_lengkap_ditolak():
    with pytest.raises(ValidationError):
        Settings(
            **_DASAR,
            STORAGE_BACKEND="s3",
            S3_ENDPOINT_URL="https://contoh.supabase.co/storage/v1/s3",
            S3_REGION="ap-southeast-1",
            S3_BUCKET="",
            S3_ACCESS_KEY_ID="kunci",
            S3_SECRET_ACCESS_KEY="rahasia",
        )


def test_db_pool_default():
    pengaturan = Settings(**_DASAR, STORAGE_BACKEND="lokal", UPLOAD_DIR="/tmp/unggahan")
    assert pengaturan.DB_POOL_SIZE == 5
    assert pengaturan.DB_MAX_OVERFLOW == 5
    assert pengaturan.DB_POOL_RECYCLE_SECONDS == 300


def test_db_pool_override():
    pengaturan = Settings(
        **_DASAR,
        STORAGE_BACKEND="lokal",
        UPLOAD_DIR="/tmp/unggahan",
        DB_POOL_SIZE=10,
        DB_MAX_OVERFLOW=0,
        DB_POOL_RECYCLE_SECONDS=60,
    )
    assert pengaturan.DB_POOL_SIZE == 10
    assert pengaturan.DB_MAX_OVERFLOW == 0
    assert pengaturan.DB_POOL_RECYCLE_SECONDS == 60
