"""Test skrip buat_admin."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Peran
from app.models.pengguna import Pengguna


@asynccontextmanager
async def _mock_sessionlocal(session: AsyncSession):
    """Context manager yang mengembalikan session dari fixture."""
    yield session


async def test_buat_admin_sukses(db_session: AsyncSession) -> None:
    """Skrip berhasil membuat akun Admin dengan kredensial valid."""
    from scripts.buat_admin import buat_admin_interaktif

    mock_sessionlocal = MagicMock()
    mock_sessionlocal.return_value.__aenter__ = AsyncMock(return_value=db_session)
    mock_sessionlocal.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        patch("scripts.buat_admin.AsyncSessionLocal", mock_sessionlocal),
    ):
        mock_input.side_effect = ["Admin Test", "admin@example.com"]
        mock_getpass.side_effect = ["password_123456", "password_123456"]

        await buat_admin_interaktif()

    # Verifikasi akun di database
    admin = await db_session.scalar(select(Pengguna).where(Pengguna.email == "admin@example.com"))
    assert admin is not None
    assert admin.nama == "Admin Test"
    assert admin.peran is Peran.ADMIN


async def test_buat_admin_email_sudah_ada(db_session: AsyncSession) -> None:
    """Skrip menolak email yang sudah terdaftar."""
    # Buat akun pertama
    from app.core.security import hash_password
    from scripts.buat_admin import buat_admin_interaktif

    pengajar = Pengguna(
        nama="Pengajar Lama",
        email="existing@example.com",
        password_hash=await hash_password("old_password_123456"),
        peran=Peran.PENGAJAR,
    )
    db_session.add(pengajar)
    await db_session.commit()

    mock_sessionlocal = MagicMock()
    mock_sessionlocal.return_value.__aenter__ = AsyncMock(return_value=db_session)
    mock_sessionlocal.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        patch("scripts.buat_admin.AsyncSessionLocal", mock_sessionlocal),
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_input.side_effect = ["Admin Test", "existing@example.com"]
        mock_getpass.side_effect = ["password_123456", "password_123456"]

        await buat_admin_interaktif()

    # Harus exit(1)
    assert exc_info.value.code == 1


async def test_buat_admin_password_terlalu_pendek(capsys) -> None:
    """Skrip menolak password < 8 karakter."""
    from scripts.buat_admin import buat_admin_interaktif

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_input.side_effect = ["Admin Test", "admin@example.com"]
        mock_getpass.side_effect = ["short", "short"]

        await buat_admin_interaktif()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "minimal 8 karakter" in captured.err


async def test_buat_admin_password_terlalu_panjang(capsys) -> None:
    """Skrip menolak password > 72 byte."""
    from scripts.buat_admin import buat_admin_interaktif

    long_password = "p" * 73  # 73 byte

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_input.side_effect = ["Admin Test", "admin@example.com"]
        mock_getpass.side_effect = [long_password, long_password]

        await buat_admin_interaktif()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "maksimal 72 karakter" in captured.err


async def test_buat_admin_password_tidak_cocok(capsys) -> None:
    """Skrip menolak password yang tidak cocok saat dikonfirmasi."""
    from scripts.buat_admin import buat_admin_interaktif

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        pytest.raises(SystemExit) as exc_info,
    ):
        mock_input.side_effect = ["Admin Test", "admin@example.com"]
        mock_getpass.side_effect = ["password_123456", "password_berbeda"]

        await buat_admin_interaktif()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "tidak cocok" in captured.err


async def test_buat_admin_password_tidak_pernah_dicetak(db_session: AsyncSession, capsys) -> None:
    """Password tidak pernah muncul di output."""
    from scripts.buat_admin import buat_admin_interaktif

    password = "my_secret_password_123456"

    mock_sessionlocal = MagicMock()
    mock_sessionlocal.return_value.__aenter__ = AsyncMock(return_value=db_session)
    mock_sessionlocal.return_value.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("builtins.input") as mock_input,
        patch("getpass.getpass") as mock_getpass,
        patch("scripts.buat_admin.AsyncSessionLocal", mock_sessionlocal),
    ):
        mock_input.side_effect = ["Admin Test", "admin@example.com"]
        mock_getpass.side_effect = [password, password]

        await buat_admin_interaktif()

    # Periksa stdout dan stderr
    captured = capsys.readouterr()
    assert password not in captured.out, "Password muncul di stdout"
    assert password not in captured.err, "Password muncul di stderr"
