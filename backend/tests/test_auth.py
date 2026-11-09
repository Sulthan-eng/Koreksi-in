import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.errors import AppError
from app.main import app
from app.models.enums import StatusLangganan
from app.models.pengguna import Pengguna
from app.models.sesi import Sesi
from app.services import auth as auth_service
from app.services import email as email_service
from app.services.langganan import jenis_akun_efektif

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


async def test_daftar_nama_kosong_setelah_strip_ditolak_sebagai_validasi_gagal(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "nama": "   "})

    assert response.status_code == 422
    assert response.json()["kode"] == "VALIDASI_GAGAL"


async def test_daftar_email_kosong_setelah_strip_ditolak_sebagai_validasi_gagal(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "email": "   "})

    assert response.status_code == 422
    assert response.json()["kode"] == "VALIDASI_GAGAL"


@pytest.mark.parametrize(
    "email",
    ["bukan-email-valid", "tanpa-domain@", "@tanpa-lokal.com", "a@b", "a b@c.com", "a@@c.com"],
)
async def test_daftar_email_format_tidak_valid_ditolak_sebagai_validasi_gagal(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str,
) -> None:
    response = await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})

    assert response.status_code == 422
    assert response.json() == {"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."}
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == email))
    assert pengguna is None


async def test_daftar_email_format_valid_diterima(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post(
        "/api/auth/daftar", json={**_DAFTAR, "email": "  Budi.S+tes@mail.sekolah.id  "}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "budi.s+tes@mail.sekolah.id"
    pengguna = await db_session.scalar(
        select(Pengguna).where(Pengguna.email == "budi.s+tes@mail.sekolah.id")
    )
    assert pengguna is not None


async def test_masuk_email_kosong_setelah_strip_ditolak_sebagai_validasi_gagal(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/auth/masuk", json={"email": "  ", "password": "rahasia123"})

    assert response.status_code == 422
    assert response.json()["kode"] == "VALIDASI_GAGAL"


async def test_daftar_integrity_error_saat_commit_dipetakan_ke_email_sudah_terdaftar(
    db_session: AsyncSession, _engine: AsyncEngine
) -> None:
    # Simulasikan race: pengguna lain berhasil mendaftar dengan email yang sama
    # tepat di antara pengecekan "email sudah ada" dan commit milik db_session.
    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    async with sessionmaker() as session_lain:
        session_lain.add(Pengguna(nama="Lain", email="budi@contoh.com", password_hash="hash-lain"))
        await session_lain.commit()

    with patch.object(db_session, "scalar", AsyncMock(return_value=None)):
        with pytest.raises(AppError) as exc_info:
            await auth_service.daftar(db_session, "Budi Santoso", "budi@contoh.com", "rahasia123")

    assert exc_info.value.kode == "EMAIL_SUDAH_TERDAFTAR"


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
    assert response.json() == {"nama": "Budi Santoso", "status_langganan": "free"}


async def test_saya_mengembalikan_status_langganan_pro(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    hasil_masuk = await _daftar_dan_masuk(client)
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.status_langganan = StatusLangganan.PRO
    await db_session.commit()

    response = await client.get(
        "/api/auth/saya", headers={"Authorization": f"Bearer {hasil_masuk['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json() == {"nama": "Budi Santoso", "status_langganan": "pro"}


def test_jenis_akun_efektif_free_pro_dan_kedaluwarsa() -> None:
    sekarang = datetime.now(UTC)
    akun_free = Pengguna(
        nama="Free",
        email="free@contoh.com",
        password_hash="h",
        status_langganan=StatusLangganan.FREE,
    )
    akun_pro_tanpa_batas = Pengguna(
        nama="Pro",
        email="pro1@contoh.com",
        password_hash="h",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=None,
    )
    akun_pro_aktif = Pengguna(
        nama="Pro Aktif",
        email="pro2@contoh.com",
        password_hash="h",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang + timedelta(days=7),
    )
    akun_pro_lewat = Pengguna(
        nama="Pro Lewat",
        email="pro3@contoh.com",
        password_hash="h",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang - timedelta(seconds=1),
    )

    assert jenis_akun_efektif(akun_free) == StatusLangganan.FREE
    assert jenis_akun_efektif(akun_pro_tanpa_batas) == StatusLangganan.PRO
    assert jenis_akun_efektif(akun_pro_aktif) == StatusLangganan.PRO
    assert jenis_akun_efektif(akun_pro_lewat) == StatusLangganan.FREE


async def test_saya_pro_dengan_masa_berlaku_lewat_mengembalikan_free(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    hasil_masuk = await _daftar_dan_masuk(client)
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.status_langganan = StatusLangganan.PRO
    pengguna.masa_berlaku_pro = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()

    response = await client.get(
        "/api/auth/saya", headers={"Authorization": f"Bearer {hasil_masuk['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json() == {"nama": "Budi Santoso", "status_langganan": "free"}


_PESAN_LUPA_PASSWORD = {"pesan": "Jika email terdaftar, tautan atur ulang password telah dikirim."}


async def test_lupa_password_email_terdaftar_dan_tidak_terdaftar_respons_sama(
    client: AsyncClient,
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)

    respons_terdaftar = await client.post(
        "/api/auth/lupa-password", json={"email": "budi@contoh.com"}
    )
    respons_tidak_terdaftar = await client.post(
        "/api/auth/lupa-password", json={"email": "tidak-ada@contoh.com"}
    )

    assert respons_terdaftar.status_code == 200
    assert respons_tidak_terdaftar.status_code == 200
    assert respons_terdaftar.json() == _PESAN_LUPA_PASSWORD
    assert respons_tidak_terdaftar.json() == _PESAN_LUPA_PASSWORD


async def test_lupa_password_format_tidak_valid_ditolak(client: AsyncClient) -> None:
    response = await client.post("/api/auth/lupa-password", json={"email": "bukan-email"})

    assert response.status_code == 422
    assert response.json() == {"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."}


async def test_lupa_password_sukses_menjadwalkan_email_dan_menyimpan_hash(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)

    response = await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})

    assert response.status_code == 200
    assert len(_background_tasks_tidak_dijalankan) == 1
    fn, args, _ = _background_tasks_tidak_dijalankan[0]
    assert fn is email_service.kirim_email_reset_password
    assert args[0] == "budi@contoh.com"

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    assert pengguna.reset_token_hash is not None
    assert pengguna.reset_dibuat_pada is not None


async def test_lupa_password_email_huruf_besar_dan_spasi_tetap_ditemukan(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)

    response = await client.post("/api/auth/lupa-password", json={"email": "  BUDI@CONTOH.com  "})

    assert response.status_code == 200
    assert len(_background_tasks_tidak_dijalankan) == 1
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    assert pengguna.reset_token_hash is not None


async def test_lupa_password_dalam_jeda_60_detik_tidak_kirim_ulang(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    hash_pertama = pengguna.reset_token_hash

    response = await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})

    assert response.status_code == 200
    assert response.json() == _PESAN_LUPA_PASSWORD
    assert len(_background_tasks_tidak_dijalankan) == 1
    await db_session.refresh(pengguna)
    assert pengguna.reset_token_hash == hash_pertama


async def test_lupa_password_permintaan_baru_setelah_jeda_menimpa_token_lama(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args_lama, _ = _background_tasks_tidak_dijalankan[0]
    token_lama = args_lama[1]

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.reset_dibuat_pada = datetime.now(UTC) - timedelta(seconds=61)
    await db_session.commit()

    response = await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})

    assert response.status_code == 200
    assert len(_background_tasks_tidak_dijalankan) == 2
    await db_session.refresh(pengguna)

    respons_token_lama = await client.post(
        "/api/auth/atur-ulang-password",
        json={"token": token_lama, "password_baru": "baru12345"},
    )
    assert respons_token_lama.status_code == 400
    assert respons_token_lama.json()["kode"] == "TOKEN_RESET_TIDAK_VALID"


async def test_atur_ulang_password_token_acak_ditolak(client: AsyncClient) -> None:
    response = await client.post(
        "/api/auth/atur-ulang-password",
        json={"token": "token-acak-tidak-valid", "password_baru": "baru12345"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "kode": "TOKEN_RESET_TIDAK_VALID",
        "pesan": "Tautan tidak berlaku atau sudah kedaluwarsa.",
    }


async def test_atur_ulang_password_token_kedaluwarsa_ditolak(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.reset_dibuat_pada = datetime.now(UTC) - timedelta(minutes=31)
    await db_session.commit()

    response = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345"}
    )

    assert response.status_code == 400
    assert response.json()["kode"] == "TOKEN_RESET_TIDAK_VALID"


async def test_atur_ulang_password_sudah_dipakai_ditolak(
    client: AsyncClient,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    sukses = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345"}
    )
    assert sukses.status_code == 204

    gagal = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345lagi"}
    )
    assert gagal.status_code == 400
    assert gagal.json()["kode"] == "TOKEN_RESET_TIDAK_VALID"


async def test_atur_ulang_password_terlalu_pendek_tidak_membakar_token(
    client: AsyncClient,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    gagal = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "pendek1"}
    )
    assert gagal.status_code == 400
    assert gagal.json()["kode"] == "PASSWORD_TERLALU_PENDEK"

    sukses = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345"}
    )
    assert sukses.status_code == 204


async def test_atur_ulang_password_terlalu_panjang_tidak_membakar_token(
    client: AsyncClient,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    gagal = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "a" * 73}
    )
    assert gagal.status_code == 400
    assert gagal.json()["kode"] == "PASSWORD_TERLALU_PANJANG"

    sukses = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345"}
    )
    assert sukses.status_code == 204


async def test_atur_ulang_password_sukses_mengubah_password_mencabut_sesi_dan_mengosongkan_kolom(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await _daftar_dan_masuk(client)
    sesi_lama = await db_session.scalar(select(Sesi))
    assert sesi_lama.dicabut_pada is None
    cookie_refresh_lama = client.cookies.get("refresh_token")

    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    response = await client.post(
        "/api/auth/atur-ulang-password", json={"token": token, "password_baru": "baru12345"}
    )
    assert response.status_code == 204

    login_lama = await client.post(
        "/api/auth/masuk", json={"email": "budi@contoh.com", "password": "rahasia123"}
    )
    assert login_lama.status_code == 401

    login_baru = await client.post(
        "/api/auth/masuk", json={"email": "budi@contoh.com", "password": "baru12345"}
    )
    assert login_baru.status_code == 200

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    assert pengguna.reset_token_hash is None
    assert pengguna.reset_dibuat_pada is None

    await db_session.refresh(sesi_lama)
    assert sesi_lama.dicabut_pada is not None

    client.cookies.set("refresh_token", cookie_refresh_lama)
    refresh_dengan_cookie_lama = await client.post("/api/auth/refresh")
    assert refresh_dengan_cookie_lama.status_code == 401


async def test_balapan_atur_ulang_password_token_sama_hanya_satu_lolos(
    client: AsyncClient,
    db_session: AsyncSession,
    _engine,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    await client.post("/api/auth/daftar", json=_DAFTAR)
    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})
    _, args, _ = _background_tasks_tidak_dijalankan[0]
    token = args[1]

    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async def _get_db_per_request() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as sesi:
            yield sesi

    override_lama = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db_per_request
    try:
        r1, r2 = await asyncio.gather(
            client.post(
                "/api/auth/atur-ulang-password",
                json={"token": token, "password_baru": "baru12345"},
            ),
            client.post(
                "/api/auth/atur-ulang-password",
                json={"token": token, "password_baru": "baru67890"},
            ),
        )
    finally:
        if override_lama is not None:
            app.dependency_overrides[get_db] = override_lama
        else:
            app.dependency_overrides.pop(get_db, None)

    assert sorted([r1.status_code, r2.status_code]) == [204, 400]
    gagal = r1 if r1.status_code == 400 else r2
    assert gagal.json()["kode"] == "TOKEN_RESET_TIDAK_VALID"

    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    assert pengguna.reset_token_hash is None


async def test_lupa_password_gagal_kirim_email_tetap_respons_generik_tanpa_500(
    client: AsyncClient,
    _background_tasks_tidak_dijalankan: list[tuple],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _kirim_smtp_gagal(pesan):
        raise OSError("gagal konek SMTP")

    monkeypatch.setattr(email_service, "_kirim_smtp", _kirim_smtp_gagal)

    await client.post("/api/auth/daftar", json=_DAFTAR)
    response = await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.com"})

    assert response.status_code == 200
    assert response.json() == _PESAN_LUPA_PASSWORD

    fn, args, kwargs = _background_tasks_tidak_dijalankan[0]
    await fn(*args, **kwargs)  # kegagalan hanya dicatat log, tidak dilempar
