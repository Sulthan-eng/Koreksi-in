from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Error domain dengan kode stabil, dipetakan ke {"kode", "pesan"} oleh handler di bawah."""

    def __init__(self, kode: str, pesan: str, status_code: int) -> None:
        self.kode = kode
        self.pesan = pesan
        self.status_code = status_code


SESI_BERAKHIR = AppError(
    kode="SESI_BERAKHIR", pesan="Sesi berakhir, silakan masuk kembali.", status_code=401
)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"kode": exc.kode, "pesan": exc.pesan})


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."},
    )
