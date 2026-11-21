"""Tes middleware BatasUkuranRequest: Content-Length, body chunked, dan interaksi
dengan CORS (413 harus tetap membawa header CORS untuk origin yang diizinkan)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import buat_app

ORIGIN_PROD = "https://app.sulthanfarizan.my.id"
_MAKS_KECIL_MB = 1


@pytest.fixture
def app_batas_kecil(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", ORIGIN_PROD)
    monkeypatch.setattr(settings, "ENV", "produksi")
    monkeypatch.setattr(settings, "MAX_REQUEST_SIZE_MB", _MAKS_KECIL_MB)
    return buat_app()


def _klien(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_content_length_melebihi_batas_ditolak_413(app_batas_kecil) -> None:
    konten_besar = b"a" * (_MAKS_KECIL_MB * 1024 * 1024 + 1)

    async with _klien(app_batas_kecil) as client:
        response = await client.post(
            "/api/auth/masuk",
            content=konten_besar,
            headers={"Content-Type": "application/octet-stream"},
        )

    assert response.status_code == 413
    assert response.json() == {
        "kode": "UKURAN_REQUEST_TERLALU_BESAR",
        "pesan": (
            "Total ukuran file yang dikirim terlalu besar. Kurangi jumlah file lalu coba lagi."
        ),
    }


async def test_body_chunked_tanpa_content_length_melebihi_batas_ditolak(
    app_batas_kecil,
) -> None:
    konten_besar = b"a" * (_MAKS_KECIL_MB * 1024 * 1024 + 1)

    async def _generator():
        tengah = len(konten_besar) // 2
        yield konten_besar[:tengah]
        yield konten_besar[tengah:]

    async with _klien(app_batas_kecil) as client:
        response = await client.post(
            "/api/auth/masuk",
            content=_generator(),
            headers={"Content-Type": "application/octet-stream"},
        )

    assert response.status_code == 413
    assert response.json()["kode"] == "UKURAN_REQUEST_TERLALU_BESAR"


async def test_request_di_bawah_batas_lewat_seperti_biasa(app_batas_kecil, db_session) -> None:
    from app.core.database import get_db

    async def _override_get_db():
        yield db_session

    app_batas_kecil.dependency_overrides[get_db] = _override_get_db
    try:
        async with _klien(app_batas_kecil) as client:
            response = await client.post(
                "/api/auth/daftar",
                json={
                    "nama": "Budi",
                    "email": "budi-batas@contoh.com",
                    "password": "rahasia123",
                },
            )
    finally:
        app_batas_kecil.dependency_overrides.pop(get_db, None)

    assert response.status_code == 201


async def test_413_membawa_header_cors_untuk_origin_diizinkan(app_batas_kecil) -> None:
    konten_besar = b"a" * (_MAKS_KECIL_MB * 1024 * 1024 + 1)

    async with _klien(app_batas_kecil) as client:
        response = await client.post(
            "/api/auth/masuk",
            content=konten_besar,
            headers={
                "Content-Type": "application/octet-stream",
                "Origin": ORIGIN_PROD,
            },
        )

    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == ORIGIN_PROD
