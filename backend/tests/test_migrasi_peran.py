"""Test migrasi add_pengguna_peran_dan_dinonaktifkan_pada."""

import os
import subprocess

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

# Gunakan database terpisah untuk migrasi
_BASE_URL = make_url(settings.DATABASE_URL)
_MIGRASI_DB_NAME = f"{_BASE_URL.database}_migrasi_test"
_MIGRASI_URL = _BASE_URL.set(database=_MIGRASI_DB_NAME)
_MAINTENANCE_URL = _BASE_URL.set(database="postgres")


def _assert_nama_db_test(nama_db: str) -> None:
    """Pastikan database untuk tes berakhir dengan _test."""
    assert nama_db.endswith("_test"), (
        f"Database uji harus berakhiran '_test', dapat {nama_db!r}. "
        "Dihentikan untuk mencegah operasi destruktif terhadap database yang salah."
    )


@pytest.fixture(scope="session")
async def _engine_migrasi() -> AsyncEngine:
    """Engine terpisah untuk tes migrasi."""
    _assert_nama_db_test(_MIGRASI_DB_NAME)

    # Buat database terpisah
    conn = await asyncpg.connect(_MAINTENANCE_URL.render_as_string(hide_password=False))
    try:
        ada = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", _MIGRASI_DB_NAME)
        if not ada:
            await conn.execute(f'CREATE DATABASE "{_MIGRASI_DB_NAME}"')
    finally:
        await conn.close()

    engine = create_async_engine(_MIGRASI_URL)
    yield engine

    # Cleanup: drop database
    _assert_nama_db_test(_MIGRASI_DB_NAME)
    await engine.dispose()
    conn = await asyncpg.connect(_MAINTENANCE_URL.render_as_string(hide_password=False))
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{_MIGRASI_DB_NAME}"')
    finally:
        await conn.close()


@pytest.mark.asyncio(scope="session")
async def test_migrasi_upgrade_downgrade(tmp_path, monkeypatch, _engine_migrasi) -> None:
    """Uji upgrade dan downgrade migrasi peran."""
    _assert_nama_db_test(_MIGRASI_DB_NAME)

    # Override DATABASE_URL untuk Alembic
    env_vars = os.environ.copy()
    env_vars["DATABASE_URL"] = _MIGRASI_URL.render_as_string(hide_password=False)

    # Upgrade ke revisi sebelumnya (d7e2c4f91a63 — reset password)
    result = subprocess.run(
        ["alembic", "upgrade", "d7e2c4f91a63"],
        cwd="backend",
        env=env_vars,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Upgrade gagal: {result.stderr}"

    # Masukkan satu baris Pengguna (data lama, tanpa peran dan dinonaktifkan_pada)
    async with _engine_migrasi.connect() as conn:
        await conn.execute(
            text(
                """
            INSERT INTO "Pengguna" (id_pengguna, nama, email, password_hash, status_langganan, dibuat_pada)
            VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Old User', 'old@example.com', 'hash', 'free', NOW())
            """
            )
        )
        await conn.commit()

        # Verifikasi baris ada sebelum migrasi
        row_before = await conn.scalar(
            text(
                "SELECT COUNT(*) FROM \"Pengguna\" WHERE id_pengguna = '550e8400-e29b-41d4-a716-446655440000'"
            )
        )
        assert row_before == 1

    # Upgrade ke head (migrasi baru)
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="backend",
        env=env_vars,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Upgrade head gagal: {result.stderr}"

    # Verifikasi kolom baru ada dan data lama tetap
    async with _engine_migrasi.connect() as conn:
        # Baris tetap ada
        row_after = await conn.scalar(
            text(
                "SELECT COUNT(*) FROM \"Pengguna\" WHERE id_pengguna = '550e8400-e29b-41d4-a716-446655440000'"
            )
        )
        assert row_after == 1

        # peran = 'pengajar'
        peran = await conn.scalar(
            text(
                "SELECT peran FROM \"Pengguna\" WHERE id_pengguna = '550e8400-e29b-41d4-a716-446655440000'"
            )
        )
        assert peran == "pengajar"

        # dinonaktifkan_pada = NULL
        dinonaktifkan = await conn.scalar(
            text(
                "SELECT dinonaktifkan_pada FROM \"Pengguna\" WHERE id_pengguna = '550e8400-e29b-41d4-a716-446655440000'"
            )
        )
        assert dinonaktifkan is None

    # Downgrade ke d7e2c4f91a63
    result = subprocess.run(
        ["alembic", "downgrade", "d7e2c4f91a63"],
        cwd="backend",
        env=env_vars,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Downgrade gagal: {result.stderr}"

    # Verifikasi kolom hilang, baris tetap
    async with _engine_migrasi.connect() as conn:
        # Baris tetap ada
        row_after_down = await conn.scalar(
            text(
                "SELECT COUNT(*) FROM \"Pengguna\" WHERE id_pengguna = '550e8400-e29b-41d4-a716-446655440000'"
            )
        )
        assert row_after_down == 1

        # Enum peran hilang dari database
        enum_exists = await conn.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'peran')")
        )
        assert not enum_exists, "Enum peran masih ada setelah downgrade"

    # Upgrade lagi ke head — ini membuktikan downgrade benar-benar menghapus enum
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd="backend",
        env=env_vars,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Upgrade ulang gagal (enum tidak dihapus): {result.stderr}"

    # Enum peran kembali ada
    async with _engine_migrasi.connect() as conn:
        enum_exists = await conn.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'peran')")
        )
        assert enum_exists, "Enum peran hilang setelah upgrade ulang"
