import json
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import (
    DataError,
    DBAPIError,
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
)
from starlette.requests import Request

from app.core.database import get_db
from app.core.errors import unexpected_error_handler
from app.main import app
from app.services import batch as batch_service

_DAFTAR = {"nama": "Budi Santoso", "email": "budi@contoh.com", "password": "rahasia123"}


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "buat_exc",
    [
        lambda: OperationalError(
            'SELECT * FROM "Batch" WHERE nama_batch = :nama',
            {"nama": "RAHASIA_PARAM_503"},
            ConnectionResetError("connection reset by peer"),
            connection_invalidated=True,
        ),
        lambda: InterfaceError(
            'SELECT * FROM "Batch" WHERE nama_batch = :nama',
            {"nama": "RAHASIA_PARAM_503"},
            RuntimeError("connection is closed"),
            connection_invalidated=False,
        ),
        lambda: DBAPIError(
            'SELECT * FROM "Batch" WHERE nama_batch = :nama',
            {"nama": "RAHASIA_PARAM_503"},
            OSError("broken pipe"),
            connection_invalidated=True,
        ),
    ],
    ids=["operational_error", "interface_error", "dbapi_connection_invalidated"],
)
async def test_dbapi_error_koneksi_mengembalikan_503_gangguan_database(
    client: AsyncClient, monkeypatch, caplog, buat_exc
) -> None:
    token = await _token(client)

    async def daftar_gagal(db, pengguna):
        raise buat_exc()

    monkeypatch.setattr(batch_service, "daftar_batch", daftar_gagal)

    with caplog.at_level("ERROR"):
        response = await client.get("/api/batch", headers=_auth(token))

    assert response.status_code == 503
    assert response.json() == {
        "kode": "GANGGUAN_DATABASE",
        "pesan": "Layanan sedang mengalami gangguan, silakan coba lagi.",
    }
    assert "RAHASIA_PARAM_503" not in response.text
    assert "RAHASIA_PARAM_503" not in caplog.text
    assert "db_error" in caplog.text


@pytest.mark.parametrize(
    "buat_exc",
    [
        lambda: IntegrityError(
            'INSERT INTO "Soal" VALUES (:kunci)',
            {"kunci": "RAHASIA_PARAM_500"},
            Exception("duplicate key value violates unique constraint"),
            connection_invalidated=False,
        ),
        lambda: DataError(
            'INSERT INTO "Soal" VALUES (:kunci)',
            {"kunci": "RAHASIA_PARAM_500"},
            Exception("value too long for type character varying"),
            connection_invalidated=False,
        ),
        lambda: ProgrammingError(
            'SELECT * FROM "Soal" WHERE kunci = :kunci',
            {"kunci": "RAHASIA_PARAM_500"},
            Exception("syntax error"),
            connection_invalidated=False,
        ),
    ],
    ids=["integrity_error", "data_error", "programming_error"],
)
async def test_dbapi_error_non_koneksi_mengembalikan_500_kesalahan_server(
    client: AsyncClient, monkeypatch, caplog, buat_exc
) -> None:
    token = await _token(client)

    async def daftar_gagal(db, pengguna):
        raise buat_exc()

    monkeypatch.setattr(batch_service, "daftar_batch", daftar_gagal)

    with caplog.at_level("ERROR"):
        response = await client.get("/api/batch", headers=_auth(token))

    assert response.status_code == 500
    assert response.json() == {
        "kode": "KESALAHAN_SERVER",
        "pesan": "Terjadi kesalahan, silakan coba lagi.",
    }
    assert "RAHASIA_PARAM_500" not in response.text
    assert "RAHASIA_PARAM_500" not in caplog.text
    assert "db_error" in caplog.text


async def test_exception_tak_terduga_mengembalikan_500_dan_mencatat_traceback(
    db_session, monkeypatch, caplog
) -> None:
    """ServerErrorMiddleware melempar ulang exception setelah mengirim respons,
    jadi tes alur ASGI memakai ASGITransport(raise_app_exceptions=False)."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            token = await _token(ac)

            async def daftar_meledak(db, pengguna):
                raise RuntimeError("detail internal rahasia 98765")

            monkeypatch.setattr(batch_service, "daftar_batch", daftar_meledak)

            with caplog.at_level("ERROR"):
                response = await ac.get("/api/batch", headers=_auth(token))
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 500
    assert response.json() == {
        "kode": "KESALAHAN_SERVER",
        "pesan": "Terjadi kesalahan, silakan coba lagi.",
    }
    assert "detail internal rahasia 98765" not in response.text
    assert "Traceback" not in response.text
    assert "unexpected_error" in caplog.text
    assert "detail internal rahasia 98765" in caplog.text
    assert any(rec.exc_info is not None for rec in caplog.records)


async def test_unexpected_error_handler_langsung(caplog) -> None:
    request = Request({"type": "http", "method": "GET", "path": "/api/contoh", "headers": []})
    with caplog.at_level("ERROR"):
        try:
            raise ValueError("detail rahasia langsung")
        except ValueError as exc:
            response = await unexpected_error_handler(request, exc)

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "kode": "KESALAHAN_SERVER",
        "pesan": "Terjadi kesalahan, silakan coba lagi.",
    }
    assert "detail rahasia langsung" not in response.body.decode()
    assert "unexpected_error" in caplog.text
    assert "detail rahasia langsung" in caplog.text


async def test_handler_global_tidak_mengubah_http_exception_validasi_dan_app_error(
    client: AsyncClient,
) -> None:
    # 1. HTTPException bawaan FastAPI (404 rute tidak ada).
    res_404_rute = await client.get("/api/rute-tidak-ada")
    assert res_404_rute.status_code == 404
    assert res_404_rute.json() == {"detail": "Not Found"}

    # 2. RequestValidationError (422 VALIDASI_GAGAL).
    res_422 = await client.post("/api/auth/daftar", json={"nama": "Budi"})
    assert res_422.status_code == 422
    assert res_422.json() == {
        "kode": "VALIDASI_GAGAL",
        "pesan": "Data yang dikirim tidak valid.",
    }

    # 3. AppError (401 SESI_BERAKHIR dan 404 BATCH_TIDAK_DITEMUKAN).
    res_401 = await client.get("/api/batch")
    assert res_401.status_code == 401
    assert res_401.json() == {
        "kode": "SESI_BERAKHIR",
        "pesan": "Sesi berakhir, silakan masuk kembali.",
    }

    token = await _token(client)
    res_404_batch = await client.get(f"/api/batch/{uuid.uuid4()}", headers=_auth(token))
    assert res_404_batch.status_code == 404
    assert res_404_batch.json() == {
        "kode": "BATCH_TIDAK_DITEMUKAN",
        "pesan": "Batch tidak ditemukan",
    }
