"""Tes visibilitas dokumentasi API (/docs, /redoc, /openapi.json) berdasarkan ENV."""

from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import buat_app

_PATH_DOCS = ("/docs", "/redoc", "/openapi.json")


def _klien(app):
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_docs_nonaktif_di_produksi(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENV", "produksi")
    app = buat_app()

    async with _klien(app) as client:
        for path in _PATH_DOCS:
            response = await client.get(path)
            assert response.status_code == 404, f"{path} harus 404 di produksi"


async def test_docs_nonaktif_pada_env_default(monkeypatch) -> None:
    default_env = type(settings).model_fields["ENV"].default
    assert default_env == "produksi"
    monkeypatch.setattr(settings, "ENV", default_env)
    app = buat_app()

    async with _klien(app) as client:
        for path in _PATH_DOCS:
            response = await client.get(path)
            assert response.status_code == 404, f"{path} harus 404 pada ENV default"


async def test_docs_aktif_di_dev(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENV", "dev")
    app = buat_app()

    async with _klien(app) as client:
        for path in _PATH_DOCS:
            response = await client.get(path)
            assert response.status_code == 200, f"{path} harus 200 di dev"

        skema = (await client.get("/openapi.json")).json()
        assert "paths" in skema
