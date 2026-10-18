from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pengguna import Pengguna
from app.models.sesi import Sesi

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}


async def _daftar_dan_masuk(client: AsyncClient, email: str = "budi@contoh.com") -> dict:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()


async def test_daftar_sukses(client: AsyncClient, db_session: AsyncSession) -> None:
    response = await client.post("/api/auth/daftar", json=_DAFTAR)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "budi@contoh.com"

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    assert pengguna is not None
    assert pengguna.password_hash != "rahasia123"


async def test_daftar_email_ganda(client: AsyncClient) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    response = await client.post("/api/auth/daftar", json=_DAFTAR)

    assert response.status_code == 409
    assert response.json() == {"kode": "EMAIL_SUDAH_TERDAFTAR", "pesan": "Email sudah terdaftar"}


async def test_daftar_password_terlalu_pendek(client: AsyncClient) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "password": "pendek1"})

    assert response.status_code == 400
    assert response.json()["kode"] == "PASSWORD_TERLALU_PENDEK"


async def test_daftar_password_terlalu_panjang(client: AsyncClient) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "password": "a" * 73})

    assert response.status_code == 400
    assert response.json()["kode"] == "PASSWORD_TERLALU_PANJANG"


async def test_daftar_field_kosong_ditolak_sebagai_validasi_gagal(client: AsyncClient) -> None:
    response = await client.post("/api/auth/daftar", json={"nama": "", "email": "", "password": ""})

    assert response.status_code == 422
    assert response.json() == {"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."}


async def test_daftar_nama_melebihi_batas_ditolak_sebagai_validasi_gagal(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "nama": "a" * 101})

    assert response.status_code == 422
    assert response.json()["kode"] == "VALIDASI_GAGAL"


async def test_daftar_race_email_ganda_ditangkap_sebagai_integrity_error(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    pengguna = Pengguna(nama="Lain", email="budi@contoh.com", password_hash="hash-lain")
    db_session.add(pengguna)
    await db_session.commit()

    response = await client.post("/api/auth/daftar", json=_DAFTAR)

    assert response.status_code == 409
    assert response.json()["kode"] == "EMAIL_SUDAH_TERDAFTAR"


async def test_masuk_sukses(client: AsyncClient, db_session: AsyncSession) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)

    response = await client.post(
        "/api/auth/masuk", json={"email": "budi@contoh.com", "password": "rahasia123"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()

    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()
    assert "path=/api/auth" in set_cookie.lower()

    sesi = await db_session.scalar(select(Sesi))
    assert sesi is not None


async def test_masuk_gagal_email_tidak_ada(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/masuk", json={"email": "tidak-ada@contoh.com", "password": "rahasia123"}
    )

    assert response.status_code == 401
    assert response.json() == {"kode": "LOGIN_GAGAL", "pesan": "Email atau password salah"}


async def test_masuk_gagal_password_salah(client: AsyncClient) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)

    response = await client.post(
        "/api/auth/masuk", json={"email": "budi@contoh.com", "password": "salah-password"}
    )

    assert response.status_code == 401
    assert response.json() == {"kode": "LOGIN_GAGAL", "pesan": "Email atau password salah"}


async def test_refresh_sukses(client: AsyncClient, db_session: AsyncSession) -> None:
    await _daftar_dan_masuk(client)
    sesi_sebelum = await db_session.scalar(select(Sesi))
    kedaluwarsa_sebelum = sesi_sebelum.kedaluwarsa_pada
    token_sebelum = sesi_sebelum.refresh_token_hash

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.json()

    await db_session.refresh(sesi_sebelum)
    assert sesi_sebelum.refresh_token_hash == token_sebelum
    assert sesi_sebelum.kedaluwarsa_pada > kedaluwarsa_sebelum


async def test_refresh_sesi_dicabut(client: AsyncClient, db_session: AsyncSession) -> None:
    await _daftar_dan_masuk(client)
    sesi = await db_session.scalar(select(Sesi))
    sesi.dicabut_pada = datetime.now(UTC)
    await db_session.commit()

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_refresh_sesi_kedaluwarsa(client: AsyncClient, db_session: AsyncSession) -> None:
    await _daftar_dan_masuk(client)
    sesi = await db_session.scalar(select(Sesi))
    sesi.kedaluwarsa_pada = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_refresh_tanpa_cookie(client: AsyncClient) -> None:
    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "kode": "SESI_BERAKHIR",
        "pesan": "Sesi berakhir, silakan masuk kembali.",
    }


async def test_keluar_mencabut_sesi(client: AsyncClient, db_session: AsyncSession) -> None:
    await _daftar_dan_masuk(client)

    response = await client.post("/api/auth/keluar")

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower()

    sesi = await db_session.scalar(select(Sesi))
    assert sesi.dicabut_pada is not None


async def test_saya_tanpa_token_ditolak(client: AsyncClient) -> None:
    response = await client.get("/api/auth/saya")

    assert response.status_code == 401
    assert response.json() == {
        "kode": "SESI_BERAKHIR",
        "pesan": "Sesi berakhir, silakan masuk kembali.",
    }


async def test_saya_dengan_sesi_dicabut_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    hasil_masuk = await _daftar_dan_masuk(client)
    sesi = await db_session.scalar(select(Sesi))
    sesi.dicabut_pada = datetime.now(UTC)
    await db_session.commit()

    response = await client.get(
        "/api/auth/saya", headers={"Authorization": f"Bearer {hasil_masuk['access_token']}"}
    )

    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_saya_dengan_token_valid(client: AsyncClient) -> None:
    hasil_masuk = await _daftar_dan_masuk(client)

    response = await client.get(
        "/api/auth/saya", headers={"Authorization": f"Bearer {hasil_masuk['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json() == {"nama": "Budi Santoso"}
