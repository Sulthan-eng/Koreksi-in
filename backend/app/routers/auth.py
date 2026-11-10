from fastapi import APIRouter, BackgroundTasks, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import pengguna_saat_ini
from app.core.errors import SESI_BERAKHIR
from app.core.security import REFRESH_TOKEN_EXPIRE_DAYS
from app.models.pengguna import Pengguna
from app.schemas.auth import (
    AturUlangPasswordRequest,
    DaftarRequest,
    DaftarResponse,
    LupaPasswordRequest,
    LupaPasswordResponse,
    MasukRequest,
    SayaResponse,
    TokenResponse,
)
from app.services import auth as auth_service
from app.services import email as email_service
from app.services.langganan import jenis_akun_efektif

router = APIRouter(prefix="/auth")

_COOKIE_NAME = "refresh_token"
_COOKIE_PATH = "/api/auth"


def _set_refresh_cookie(response: Response, token: str, secure: bool) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path=_COOKIE_PATH,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        secure=secure,
    )


@router.post("/daftar", response_model=DaftarResponse, status_code=201)
async def daftar(body: DaftarRequest, db: AsyncSession = Depends(get_db)) -> DaftarResponse:
    pengguna = await auth_service.daftar(db, body.nama, body.email, body.password)
    return DaftarResponse(
        id_pengguna=pengguna.id_pengguna, nama=pengguna.nama, email=pengguna.email
    )


@router.post("/masuk", response_model=TokenResponse)
async def masuk(
    body: MasukRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    access_token, refresh_token = await auth_service.masuk(db, body.email, body.password)
    _set_refresh_cookie(response, refresh_token, settings.COOKIE_SECURE)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    refresh_token = request.cookies.get(_COOKIE_NAME)
    if refresh_token is None:
        raise SESI_BERAKHIR

    access_token = await auth_service.refresh(db, refresh_token)
    _set_refresh_cookie(response, refresh_token, settings.COOKIE_SECURE)
    return TokenResponse(access_token=access_token)


@router.post("/keluar", status_code=204)
async def keluar(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> None:
    refresh_token = request.cookies.get(_COOKIE_NAME)
    await auth_service.keluar(db, refresh_token)
    response.delete_cookie(key=_COOKIE_NAME, path=_COOKIE_PATH)


@router.get("/saya", response_model=SayaResponse)
async def saya(pengguna: Pengguna = Depends(pengguna_saat_ini)) -> SayaResponse:
    return SayaResponse(nama=pengguna.nama, status_langganan=jenis_akun_efektif(pengguna))


@router.post("/lupa-password", response_model=LupaPasswordResponse)
async def lupa_password(
    body: LupaPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> LupaPasswordResponse:
    hasil = await auth_service.minta_reset_password(db, body.email)
    if hasil is not None:
        pengguna, token_mentah = hasil
        background_tasks.add_task(
            email_service.kirim_email_reset_password, pengguna.email, token_mentah
        )
    return LupaPasswordResponse()


@router.post("/atur-ulang-password", status_code=204)
async def atur_ulang_password(
    body: AturUlangPasswordRequest, db: AsyncSession = Depends(get_db)
) -> None:
    await auth_service.atur_ulang_password(db, body.token, body.password_baru)
