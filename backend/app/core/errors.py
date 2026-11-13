from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
