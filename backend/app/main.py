import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.core.cors import asal_diizinkan
from app.core.database import AsyncSessionLocal
from app.core.errors import (
    AppError,
    app_error_handler,
    db_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)
from app.core.logging import atur_logging
from app.core.middleware import BatasUkuranRequest
from app.core.startup import sapu_proses_tergantung
from app.routers import admin, auth, batch, health, langganan, midtrans, ringkasan

logger = logging.getLogger(__name__)

# Method dan header diizinkan secara eksplisit (tanpa wildcard). Daftarnya persis
# apa yang dipakai aplikasi: method dari router di app/routers/, header dari
# frontend/src/api/klien.js yang hanya menyetel Authorization dan Content-Type.
METHOD_DIIZINKAN = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
HEADER_DIIZINKAN = ["Authorization", "Content-Type"]
HEADER_DIEKSPOS = ["Content-Disposition"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("storage_backend_aktif backend=%s", settings.STORAGE_BACKEND)
    async with AsyncSessionLocal() as db:
        await sapu_proses_tergantung(db)
    yield


def buat_app() -> FastAPI:
    """Bangun aplikasi. Dibuat sebagai factory karena daftar origin, batas ukuran,
    dan visibilitas dokumentasi API dibaca saat konstruksi, sehingga test bisa
    membangun varian (ENV=produksi/dev, batas kecil) tanpa mengandalkan urutan import."""
    atur_logging()
    tampilkan_docs = settings.ENV != "produksi"
    app = FastAPI(
        title="Koreksi-in",
        lifespan=lifespan,
        docs_url="/docs" if tampilkan_docs else None,
        redoc_url="/redoc" if tampilkan_docs else None,
        openapi_url="/openapi.json" if tampilkan_docs else None,
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(DBAPIError, db_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)

    # Urutan penting: add_middleware menaruh yang terakhir ditambahkan di posisi
    # paling luar, jadi CORSMiddleware membungkus BatasUkuranRequest dan respons 413
    # dari batas ukuran ikut membawa header CORS.
    app.add_middleware(BatasUkuranRequest, maks_byte=settings.MAX_REQUEST_SIZE_MB * 1024 * 1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=asal_diizinkan(),
        allow_credentials=True,
        allow_methods=METHOD_DIIZINKAN,
        allow_headers=HEADER_DIIZINKAN,
        expose_headers=HEADER_DIEKSPOS,
        max_age=600,
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(batch.router, prefix="/api")
    app.include_router(ringkasan.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(langganan.router, prefix="/api")
    app.include_router(midtrans.router, prefix="/api")
    return app


app = buat_app()
