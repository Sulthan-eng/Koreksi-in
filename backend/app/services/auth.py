from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import SESI_BERAKHIR, AppError
from app.core.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    buat_access_token,
    buat_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.pengguna import Pengguna
from app.models.sesi import Sesi

EMAIL_SUDAH_TERDAFTAR = AppError(
    kode="EMAIL_SUDAH_TERDAFTAR", pesan="Email sudah terdaftar", status_code=409
)
PASSWORD_TERLALU_PENDEK = AppError(
    kode="PASSWORD_TERLALU_PENDEK", pesan="Password minimal 8 karakter", status_code=400
)
PASSWORD_TERLALU_PANJANG = AppError(
    kode="PASSWORD_TERLALU_PANJANG", pesan="Password maksimal 72 karakter", status_code=400
)
LOGIN_GAGAL = AppError(kode="LOGIN_GAGAL", pesan="Email atau password salah", status_code=401)


async def daftar(db: AsyncSession, nama: str, email: str, password: str) -> Pengguna:
    email = email.strip().lower()
    panjang_password = len(password.encode("utf-8"))
    if panjang_password < 8:
        raise PASSWORD_TERLALU_PENDEK
    if panjang_password > 72:
        raise PASSWORD_TERLALU_PANJANG

    existing = await db.scalar(select(Pengguna).where(Pengguna.email == email))
    if existing is not None:
        raise EMAIL_SUDAH_TERDAFTAR

    pengguna = Pengguna(nama=nama, email=email, password_hash=await hash_password(password))
    db.add(pengguna)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise EMAIL_SUDAH_TERDAFTAR from None
    return pengguna


async def masuk(db: AsyncSession, email: str, password: str) -> tuple[str, str]:
    email = email.strip().lower()
    pengguna = await db.scalar(select(Pengguna).where(Pengguna.email == email))
    if pengguna is None or not await verify_password(password, pengguna.password_hash):
        raise LOGIN_GAGAL

    sekarang = datetime.now(UTC)
    token_mentah, token_hash = buat_refresh_token()
    sesi = Sesi(
        id_pengguna=pengguna.id_pengguna,
        refresh_token_hash=token_hash,
        terakhir_dipakai_pada=sekarang,
        kedaluwarsa_pada=sekarang + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(sesi)
    await db.commit()

    access_token = buat_access_token(pengguna.id_pengguna, sesi.id_sesi)
    return access_token, token_mentah


async def refresh(db: AsyncSession, refresh_token: str) -> str:
    token_hash = hash_refresh_token(refresh_token)
    sekarang = datetime.now(UTC)
    sesi = await db.scalar(
        select(Sesi).where(
            Sesi.refresh_token_hash == token_hash,
            Sesi.dicabut_pada.is_(None),
            Sesi.kedaluwarsa_pada > sekarang,
        )
    )
    if sesi is None:
        raise SESI_BERAKHIR

    sesi.terakhir_dipakai_pada = sekarang
    sesi.kedaluwarsa_pada = sekarang + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    await db.commit()

    return buat_access_token(sesi.id_pengguna, sesi.id_sesi)


async def keluar(db: AsyncSession, refresh_token: str | None) -> None:
    if refresh_token is None:
        return
    token_hash = hash_refresh_token(refresh_token)
    sesi = await db.scalar(select(Sesi).where(Sesi.refresh_token_hash == token_hash))
    if sesi is not None and sesi.dicabut_pada is None:
        sesi.dicabut_pada = datetime.now(UTC)
        await db.commit()
