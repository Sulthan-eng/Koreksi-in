from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base

_BASE_URL = make_url(settings.DATABASE_URL)
_TEST_DB_NAME = f"{_BASE_URL.database}_test"


def _assert_nama_db_test(nama_db: str) -> None:
    assert nama_db.endswith("_test"), (
        f"Database uji harus berakhiran '_test', dapat {nama_db!r}. "
        "Dihentikan untuk mencegah operasi destruktif terhadap database yang salah."
    )


_assert_nama_db_test(_TEST_DB_NAME)

_TEST_URL = _BASE_URL.set(database=_TEST_DB_NAME, drivername="postgresql+asyncpg")
_MAINTENANCE_URL = _BASE_URL.set(database="postgres", drivername="postgresql")


async def _pastikan_database_uji_ada() -> None:
    conn = await asyncpg.connect(_MAINTENANCE_URL.render_as_string(hide_password=False))
    try:
        ada = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB_NAME)
        if not ada:
            await conn.execute(f'CREATE DATABASE "{_TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _engine() -> AsyncGenerator:
    _assert_nama_db_test(_TEST_DB_NAME)
    await _pastikan_database_uji_ada()

    engine = create_async_engine(_TEST_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    _assert_nama_db_test(_TEST_DB_NAME)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(_engine) -> AsyncGenerator[AsyncSession, None]:
    _assert_nama_db_test(_TEST_DB_NAME)
    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session

    _assert_nama_db_test(_TEST_DB_NAME)
    async with _engine.begin() as conn:
        await conn.exec_driver_sql('TRUNCATE TABLE "Sesi", "Pengguna" RESTART IDENTITY CASCADE')


@pytest.fixture(autouse=True)
def _background_tasks_tidak_dijalankan(monkeypatch) -> list[tuple]:
    """Cegah BackgroundTasks benar-benar berjalan (Gemini + database pengembangan) saat test
    memanggil endpoint unggah. Starlette menjalankan BackgroundTasks di akhir siklus request
    yang sama, jadi tanpa ini test unggah akan memicu panggilan Gemini sungguhan dan membuka
    koneksi ke database pengembangan lewat AsyncSessionLocal. Dipatch di level BackgroundTasks
    (bukan pemrosesan.proses_file_jawaban) agar test yang memanggil pemrosesan langsung (tanpa
    lewat router) tidak ikut terdampak, karena keduanya memakai objek modul yang sama."""
    dijadwalkan: list[tuple] = []

    def _add_task_palsu(self, func, *args, **kwargs):
        dijadwalkan.append((func, args, kwargs))

    monkeypatch.setattr(BackgroundTasks, "add_task", _add_task_palsu)
    return dijadwalkan


@pytest_asyncio.fixture(loop_scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)
