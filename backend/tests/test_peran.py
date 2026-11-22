"""Test peran dan penjagaan akses rute."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import admin_saat_ini, pengajar_saat_ini
from app.core.security import hash_password
from app.main import app
from app.models.enums import Peran
from app.models.pengguna import Pengguna

# Rute publik tanpa autentikasi
RUTE_PUBLIK = {
    ("GET", "/api/health"),
    ("POST", "/api/auth/daftar"),
    ("POST", "/api/auth/masuk"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/keluar"),
    ("POST", "/api/auth/lupa-password"),
    ("POST", "/api/auth/atur-ulang-password"),
}

# Rute bersama untuk kedua peran
RUTE_BERSAMA = {
    ("GET", "/api/auth/saya"),
}

# Rute khusus Pengajar (Admin ditolak 403)
RUTE_PENGAJAR = {
    ("GET", "/api/batch"),
    ("POST", "/api/batch"),
    ("GET", "/api/batch/{id_batch}"),
    ("DELETE", "/api/batch/{id_batch}"),
    ("POST", "/api/batch/{id_batch}/selesaikan"),
    ("GET", "/api/batch/{id_batch}/soal"),
    ("POST", "/api/batch/{id_batch}/soal"),
    ("POST", "/api/batch/{id_batch}/soal/ocr-kunci"),
    ("GET", "/api/batch/{id_batch}/file-jawaban"),
    ("POST", "/api/batch/{id_batch}/file-jawaban"),
    ("POST", "/api/batch/{id_batch}/file-jawaban/{id_file}/coba-lagi"),
    ("GET", "/api/batch/{id_batch}/hasil"),
    ("PATCH", "/api/batch/{id_batch}/hasil/{id_koreksi}"),
    ("PATCH", "/api/batch/{id_batch}/hasil/{id_koreksi}/nilai-akhir"),
    ("GET", "/api/batch/{id_batch}/ekspor"),
    ("GET", "/api/ringkasan"),
}

# Rute khusus Admin (Pengajar ditolak 403)
RUTE_ADMIN = {
    ("GET", "/api/admin/akun-pengajar"),
    ("PATCH", "/api/admin/akun-pengajar/{id_pengguna}/langganan"),
    ("POST", "/api/admin/akun-pengajar/{id_pengguna}/nonaktifkan"),
    ("POST", "/api/admin/akun-pengajar/{id_pengguna}/aktifkan"),
}


def _rute_dari_app() -> set[tuple[str, str]]:
    """Ekstrak daftar (method, path) dari OpenAPI spec."""
    rute_set = set()
    openapi = app.openapi()
    if not openapi:
        return rute_set

    paths = openapi.get("paths", {})
    for path, path_item in paths.items():
        # path_item adalah dict dengan keys seperti "get", "post", "patch", "delete"
        for method in path_item.keys():
            if method.upper() not in {"HEAD", "OPTIONS"}:
                rute_set.add((method.upper(), path))
    return rute_set


def test_semua_rute_terklasifikasi() -> None:
    """Pastikan setiap rute sudah diklasifikasikan sebagai publik, bersama, Pengajar, atau Admin."""
    rute_app = _rute_dari_app()
    rute_diketahui = RUTE_PUBLIK | RUTE_BERSAMA | RUTE_PENGAJAR | RUTE_ADMIN

    rute_tidak_diketahui = rute_app - rute_diketahui
    assert not rute_tidak_diketahui, (
        f"Rute baru tidak terklasifikasi: {sorted(rute_tidak_diketahui)}"
    )

    rute_tidak_ada = rute_diketahui - rute_app
    assert not rute_tidak_ada, f"Rute di daftar tidak ada di app: {sorted(rute_tidak_ada)}"


def _cari_rute_app(method: str, path: str):
    for included_route in app.routes:
        if hasattr(included_route, "original_router") and hasattr(
            included_route, "include_context"
        ):
            prefix = included_route.include_context.prefix or ""
            for r in included_route.original_router.routes:
                if hasattr(r, "path") and hasattr(r, "methods"):
                    full_path = prefix + r.path
                    if full_path == path and method in r.methods:
                        return r
    return None


def _kumpulkan_dependensi_rute(rute) -> tuple[set[str], set[str]]:
    semua: set[str] = set()
    tingkat_pertama: set[str] = set()
    if not (hasattr(rute, "dependant") and rute.dependant):
        return semua, tingkat_pertama

    def _telusuri(dep, level: int) -> None:
        if hasattr(dep, "dependencies") and dep.dependencies:
            for sub_dep in dep.dependencies:
                if hasattr(sub_dep, "call") and sub_dep.call:
                    try:
                        nama = sub_dep.call.__name__
                    except AttributeError:
                        nama = sub_dep.call.__class__.__name__
                    semua.add(nama)
                    if level == 0:
                        tingkat_pertama.add(nama)
                _telusuri(sub_dep, level + 1)

    _telusuri(rute.dependant, 0)
    return semua, tingkat_pertama


def test_rute_pengajar_memakai_dependensi_pengajar() -> None:
    """Telusuri dependensi rute Pengajar dan pastikan pengajar_saat_ini dipakai tingkat pertama."""
    for method, path in sorted(RUTE_PENGAJAR):
        rute = _cari_rute_app(method, path)
        assert rute is not None, f"Rute {method} {path} tidak ditemukan di app"
        dependensi_names, first_level_deps = _kumpulkan_dependensi_rute(rute)
        assert "pengajar_saat_ini" in dependensi_names, (
            f"{method} {path} tidak memakai pengajar_saat_ini"
        )
        assert "pengguna_saat_ini" not in first_level_deps, (
            f"{method} {path} memakai pengguna_saat_ini langsung (harus via pengajar_saat_ini)"
        )


def test_rute_admin_memakai_dependensi_admin() -> None:
    """Pastikan rute Admin memakai admin_saat_ini tanpa pengguna_saat_ini langsung."""
    for method, path in sorted(RUTE_ADMIN):
        rute = _cari_rute_app(method, path)
        assert rute is not None, f"Rute {method} {path} tidak ditemukan di app"
        dependensi_names, first_level_deps = _kumpulkan_dependensi_rute(rute)
        assert "admin_saat_ini" in dependensi_names, f"{method} {path} tidak memakai admin_saat_ini"
        assert "pengguna_saat_ini" not in first_level_deps, (
            f"{method} {path} memakai pengguna_saat_ini langsung (harus via admin_saat_ini)"
        )


@pytest.mark.parametrize("method,path", sorted(RUTE_PENGAJAR))
async def test_rute_pengajar_menolak_admin(
    client: AsyncClient, db_session: AsyncSession, method: str, path: str
) -> None:
    """Admin ditolak 403 pada semua rute Pengajar."""
    # Buat akun Admin
    id_admin = uuid.uuid4()
    password_hash = await hash_password("admin_password_123456")
    admin = Pengguna(
        id_pengguna=id_admin,
        nama="Admin Test",
        email="admin.test@example.com",
        password_hash=password_hash,
        peran=Peran.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    # Login sebagai Admin
    response = await client.post(
        "/api/auth/masuk",
        json={"email": "admin.test@example.com", "password": "admin_password_123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ganti UUID di path dengan nilai random (rute akan 403 di dependensi, tidak 404)
    path_actual = (
        path.replace("{id_batch}", str(uuid.uuid4()))
        .replace("{id_file}", str(uuid.uuid4()))
        .replace("{id_koreksi}", str(uuid.uuid4()))
    )

    # Panggil endpoint sebagai Admin
    if method == "GET":
        response = await client.get(path_actual, headers=headers)
    elif method == "POST":
        response = await client.post(path_actual, json={}, headers=headers)
    elif method == "PATCH":
        response = await client.patch(path_actual, json={}, headers=headers)
    elif method == "DELETE":
        response = await client.delete(path_actual, headers=headers)
    else:
        pytest.fail(f"Method tidak dikenal: {method}")

    # 403 dengan kode AKSES_DITOLAK
    assert response.status_code == 403, (
        f"{method} {path} tidak 403, dapat {response.status_code}: {response.text}"
    )
    body = response.json()
    assert body.get("kode") == "AKSES_DITOLAK", f"Kode error salah: {body}"


@pytest.mark.parametrize("method,path", sorted(RUTE_ADMIN))
async def test_rute_admin_menolak_pengajar(
    client: AsyncClient, db_session: AsyncSession, method: str, path: str
) -> None:
    """Pengajar ditolak 403 pada semua rute Admin."""
    pengajar = Pengguna(
        id_pengguna=uuid.uuid4(),
        nama="Pengajar Test",
        email="pengajar.rute@example.com",
        password_hash=await hash_password("pengajar_pass_123456"),
        peran=Peran.PENGAJAR,
    )
    db_session.add(pengajar)
    await db_session.commit()

    response = await client.post(
        "/api/auth/masuk",
        json={"email": "pengajar.rute@example.com", "password": "pengajar_pass_123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    path_actual = path.replace("{id_pengguna}", str(uuid.uuid4()))

    if method == "GET":
        response = await client.get(path_actual, headers=headers)
    elif method == "POST":
        response = await client.post(path_actual, json={}, headers=headers)
    elif method == "PATCH":
        response = await client.patch(path_actual, json={}, headers=headers)
    elif method == "DELETE":
        response = await client.delete(path_actual, headers=headers)
    else:
        pytest.fail(f"Method tidak dikenal: {method}")

    assert response.status_code == 403, (
        f"{method} {path} tidak 403, dapat {response.status_code}: {response.text}"
    )
    assert response.json().get("kode") == "AKSES_DITOLAK"


async def test_rute_bersama_menerima_kedua_peran(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Rute bersama (GET /saya) diterima oleh Admin dan Pengajar."""
    # Buat Pengajar
    id_pengajar = uuid.uuid4()
    password_hash_pengajar = await hash_password("pengajar_pass_123456")
    pengajar = Pengguna(
        id_pengguna=id_pengajar,
        nama="Pengajar Test",
        email="pengajar.test@example.com",
        password_hash=password_hash_pengajar,
        peran=Peran.PENGAJAR,
    )
    db_session.add(pengajar)

    # Buat Admin
    id_admin = uuid.uuid4()
    password_hash_admin = await hash_password("admin_pass_123456")
    admin = Pengguna(
        id_pengguna=id_admin,
        nama="Admin Test",
        email="admin.test@example.com",
        password_hash=password_hash_admin,
        peran=Peran.ADMIN,
    )
    db_session.add(admin)
    await db_session.commit()

    # Pengajar: GET /saya → 200, peran pengajar
    resp_pengajar = await client.post(
        "/api/auth/masuk",
        json={"email": "pengajar.test@example.com", "password": "pengajar_pass_123456"},
    )
    token_pengajar = resp_pengajar.json()["access_token"]
    resp = await client.get("/api/auth/saya", headers={"Authorization": f"Bearer {token_pengajar}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["peran"] == "pengajar"

    # Admin: GET /saya → 200, peran admin
    resp_admin = await client.post(
        "/api/auth/masuk", json={"email": "admin.test@example.com", "password": "admin_pass_123456"}
    )
    token_admin = resp_admin.json()["access_token"]
    resp = await client.get("/api/auth/saya", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["peran"] == "admin"


async def test_admin_saat_ini_menolak_pengajar(db_session: AsyncSession) -> None:
    """Dependensi admin_saat_ini menolak Pengajar."""
    # Buat Pengajar
    id_pengajar = uuid.uuid4()
    password_hash = await hash_password("test_pass_123456")
    pengajar = Pengguna(
        id_pengguna=id_pengajar,
        nama="Pengajar Test",
        email="pengajar.test@example.com",
        password_hash=password_hash,
        peran=Peran.PENGAJAR,
    )
    db_session.add(pengajar)
    await db_session.commit()

    # Ambil Pengguna dari DB
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.id_pengguna == id_pengajar))

    # Panggil admin_saat_ini → harus raise AKSES_DITOLAK
    from app.core.dependencies import AKSES_DITOLAK

    with pytest.raises(Exception) as exc_info:
        await admin_saat_ini(pengguna)

    assert exc_info.value is AKSES_DITOLAK


async def test_pengajar_saat_ini_menerima_pengajar(db_session: AsyncSession) -> None:
    """Dependensi pengajar_saat_ini menerima Pengajar."""
    # Buat Pengajar
    id_pengajar = uuid.uuid4()
    password_hash = await hash_password("test_pass_123456")
    pengajar = Pengguna(
        id_pengguna=id_pengajar,
        nama="Pengajar Test",
        email="pengajar.test@example.com",
        password_hash=password_hash,
        peran=Peran.PENGAJAR,
    )
    db_session.add(pengajar)
    await db_session.commit()

    # Ambil dari DB
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.id_pengguna == id_pengajar))

    # Panggil pengajar_saat_ini → harus return pengguna
    hasil = await pengajar_saat_ini(pengguna)
    assert hasil.id_pengguna == id_pengajar
    assert hasil.peran is Peran.PENGAJAR
