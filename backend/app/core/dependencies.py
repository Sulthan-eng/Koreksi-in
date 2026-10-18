import uuid
from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import SESI_BERAKHIR
from app.core.security import verifikasi_access_token
from app.models.pengguna import Pengguna
from app.models.sesi import Sesi

_bearer = HTTPBearer(auto_error=False)


async def pengguna_saat_ini(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Pengguna:
    if credentials is None:
        raise SESI_BERAKHIR

    payload = verifikasi_access_token(credentials.credentials)
    id_sesi = uuid.UUID(payload["id_sesi"])
    id_pengguna = uuid.UUID(payload["id_pengguna"])

    sesi = await db.scalar(
        select(Sesi).where(
            Sesi.id_sesi == id_sesi,
            Sesi.dicabut_pada.is_(None),
            Sesi.kedaluwarsa_pada > datetime.now(UTC),
        )
    )
    if sesi is None:
        raise SESI_BERAKHIR

    pengguna = await db.scalar(select(Pengguna).where(Pengguna.id_pengguna == id_pengguna))
    if pengguna is None:
        raise SESI_BERAKHIR

    return pengguna
