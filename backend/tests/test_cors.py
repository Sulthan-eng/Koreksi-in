"""Tes CORS: origin diizinkan vs ditolak, preflight, kredensial, header pada 500.

Memakai buat_app() (bukan app module-level) karena daftar origin dibaca saat
konstruksi FastAPI lewat CORSMiddleware; app yang sudah dibangun tidak bisa
diubah originnya lewat monkeypatch settings setelah fakta. /api/health dipakai
sebagai target karena tidak butuh database, cocok untuk ASGITransport tanpa
override get_db maupun lifespan (lifespan tidak berjalan di ASGITransport).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import buat_app

ORIGIN_PROD = "https://app.sulthanfarizan.my.id"
ORIGIN_ASING = "https://penyerang.contoh.com"
ORIGIN_DEV = "http://localhost:5173"


def _klien(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def app_produksi(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", ORIGIN_PROD)
    monkeypatch.setattr(settings, "ENV", "produksi")
    return buat_app()


@pytest.fixture
def app_dev(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", ORIGIN_PROD)
    monkeypatch.setattr(settings, "ENV", "dev")
    return buat_app()


async def test_preflight_origin_diizinkan_dikembalikan_lengkap(app_produksi) -> None:
    async with _klien(app_produksi) as client:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": ORIGIN_PROD,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN_PROD
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "GET" in response.headers["access-control-allow-methods"]
    header_diizinkan = response.headers["access-control-allow-headers"].lower()
    assert "authorization" in header_diizinkan
    assert "content-type" in header_diizinkan
    assert "*" not in response.headers["access-control-allow-methods"]
    assert "*" not in header_diizinkan


async def test_preflight_origin_ditolak_tanpa_header_izin(app_produksi) -> None:
    async with _klien(app_produksi) as client:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": ORIGIN_ASING,
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers


async def test_preflight_header_tidak_diizinkan_ditolak(app_produksi) -> None:
    async with _klien(app_produksi) as client:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": ORIGIN_PROD,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-apa-saja",
            },
        )

    assert "access-control-allow-headers" not in response.headers or (
        "x-apa-saja" not in response.headers.get("access-control-allow-headers", "").lower()
    )


async def test_request_sungguhan_origin_diizinkan_membawa_header(app_produksi) -> None:
    async with _klien(app_produksi) as client:
        response = await client.get("/api/health", headers={"Origin": ORIGIN_PROD})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN_PROD
    assert response.headers["vary"] == "Origin"
    assert "content-disposition" in response.headers["access-control-expose-headers"].lower()


async def test_request_sungguhan_origin_ditolak_tanpa_header(app_produksi) -> None:
    async with _klien(app_produksi) as client:
        response = await client.get("/api/health", headers={"Origin": ORIGIN_ASING})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


async def test_localhost_diizinkan_hanya_di_luar_produksi(app_dev, app_produksi) -> None:
    async with _klien(app_dev) as client:
        respons_dev = await client.get("/api/health", headers={"Origin": ORIGIN_DEV})
    async with _klien(app_produksi) as client:
        respons_produksi = await client.get("/api/health", headers={"Origin": ORIGIN_DEV})

    assert respons_dev.headers["access-control-allow-origin"] == ORIGIN_DEV
    assert "access-control-allow-origin" not in respons_produksi.headers


async def test_env_default_adalah_produksi_dan_menolak_localhost(monkeypatch) -> None:
    default_env = type(settings).model_fields["ENV"].default
    assert default_env == "produksi", "default ENV harus gagal-aman (produksi)"

    monkeypatch.setattr(settings, "FRONTEND_URL", ORIGIN_PROD)
    monkeypatch.setattr(settings, "ENV", default_env)
    app = buat_app()

    async with _klien(app) as client:
        response = await client.get("/api/health", headers={"Origin": ORIGIN_DEV})

    assert "access-control-allow-origin" not in response.headers


async def test_frontend_url_trailing_slash_dinormalisasi(monkeypatch) -> None:
    monkeypatch.setattr(settings, "FRONTEND_URL", ORIGIN_PROD + "/")
    monkeypatch.setattr(settings, "ENV", "produksi")
    app = buat_app()

    async with _klien(app) as client:
        response = await client.get("/api/health", headers={"Origin": ORIGIN_PROD})

    assert response.headers["access-control-allow-origin"] == ORIGIN_PROD


async def test_respons_500_membawa_header_cors_untuk_origin_diizinkan(
    app_produksi, db_session, monkeypatch
) -> None:
    """Handler Exception (ServerErrorMiddleware) berada di luar CORSMiddleware,
    jadi ini menutup kasus yang sebelumnya tampil sebagai "network error" di browser."""
    from app.core.database import get_db
    from app.services import batch as batch_service

    async def _override_get_db():
        yield db_session

    app_produksi.dependency_overrides[get_db] = _override_get_db

    async def daftar_meledak(db, pengguna):
        raise RuntimeError("meledak sengaja untuk tes")

    monkeypatch.setattr(batch_service, "daftar_batch", daftar_meledak)

    from httpx import ASGITransport as _AT

    transport = _AT(app=app_produksi, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/daftar",
                json={"nama": "Budi", "email": "budi500@contoh.com", "password": "rahasia123"},
            )
            token_resp = await client.post(
                "/api/auth/masuk",
                json={"email": "budi500@contoh.com", "password": "rahasia123"},
            )
            token = token_resp.json()["access_token"]

            response_diizinkan = await client.get(
                "/api/batch",
                headers={"Authorization": f"Bearer {token}", "Origin": ORIGIN_PROD},
            )
            response_ditolak = await client.get(
                "/api/batch",
                headers={"Authorization": f"Bearer {token}", "Origin": ORIGIN_ASING},
            )
    finally:
        app_produksi.dependency_overrides.pop(get_db, None)

    assert response_diizinkan.status_code == 500
    assert response_diizinkan.headers["access-control-allow-origin"] == ORIGIN_PROD
    assert response_diizinkan.headers["access-control-allow-credentials"] == "true"

    assert response_ditolak.status_code == 500
    assert "access-control-allow-origin" not in response_ditolak.headers
