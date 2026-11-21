import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError

from app.core.cors import header_cors

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Error domain dengan kode stabil, dipetakan ke {"kode", "pesan"} oleh handler di bawah."""

    def __init__(
        self, kode: str, pesan: str, status_code: int, extra: dict[str, Any] | None = None
    ) -> None:
        self.kode = kode
        self.pesan = pesan
        self.status_code = status_code
        self.extra = extra


SESI_BERAKHIR = AppError(
    kode="SESI_BERAKHIR", pesan="Sesi berakhir, silakan masuk kembali.", status_code=401
)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # extra ditulis dulu lalu kode/pesan menimpa, agar extra tidak pernah bisa
    # mengganti field "kode" atau "pesan" tingkat atas.
    content: dict[str, Any] = {**(exc.extra or {}), "kode": exc.kode, "pesan": exc.pesan}
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."},
    )


async def db_error_handler(request: Request, exc: DBAPIError) -> JSONResponse:
    # Catat metadata aman saja (tanpa str(exc)/params SQL agar teks jawaban,
    # kunci jawaban, atau hash kredensial tidak pernah bocor ke log).
    orig_tipe = type(exc.orig).__name__ if exc.orig is not None else "none"
    logger.error(
        "db_error method=%s path=%s tipe=%s orig=%s connection_invalidated=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        orig_tipe,
        exc.connection_invalidated,
    )
    if exc.connection_invalidated or isinstance(exc, OperationalError | InterfaceError):
        return JSONResponse(
            status_code=503,
            content={
                "kode": "GANGGUAN_DATABASE",
                "pesan": "Layanan sedang mengalami gangguan, silakan coba lagi.",
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "kode": "KESALAHAN_SERVER",
            "pesan": "Terjadi kesalahan, silakan coba lagi.",
        },
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected_error method=%s path=%s", request.method, request.url.path)
    # Handler Exception dipasang Starlette di ServerErrorMiddleware, di luar
    # CORSMiddleware, jadi respons ini tidak pernah melewatinya. Tanpa header di
    # bawah, galat 500 tampil di browser sebagai "network error" alih-alih pesan
    # aplikasi. Daftar origin diambil dari app.core.cors agar tetap satu sumber.
    return JSONResponse(
        status_code=500,
        content={
            "kode": "KESALAHAN_SERVER",
            "pesan": "Terjadi kesalahan, silakan coba lagi.",
        },
        headers=header_cors(request.headers.get("origin")),
    )
