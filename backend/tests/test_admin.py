import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.batch import Batch
from app.models.enums import Peran, StatusBatch, StatusLangganan
from app.models.pengguna import Pengguna
from app.models.sesi import Sesi
from app.services.langganan import TZ_WIB, jenis_akun_efektif


async def _buat_pengguna(
    db_session: AsyncSession,
    *,
    nama: str,
    email: str,
    password: str = "rahasia123",
    peran: Peran = Peran.PENGAJAR,
    status_langganan: StatusLangganan = StatusLangganan.FREE,
    masa_berlaku_pro: datetime | None = None,
    dinonaktifkan_pada: datetime | None = None,
    dibuat_pada: datetime | None = None,
) -> Pengguna:
    pengguna = Pengguna(
        nama=nama,
        email=email,
        password_hash=await hash_password(password),
        peran=peran,
        status_langganan=status_langganan,
        masa_berlaku_pro=masa_berlaku_pro,
        dinonaktifkan_pada=dinonaktifkan_pada,
    )
    if dibuat_pada is not None:
        pengguna.dibuat_pada = dibuat_pada
    db_session.add(pengguna)
    await db_session.commit()
    await db_session.refresh(pengguna)
    return pengguna


async def _masuk(client: AsyncClient, email: str, password: str = "rahasia123") -> str:
    response = await client.post("/api/auth/masuk", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _token_admin(
    client: AsyncClient, db_session: AsyncSession, email: str = "admin@contoh.id"
) -> tuple[Pengguna, dict[str, str]]:
    admin = await _buat_pengguna(db_session, nama="Admin Utama", email=email, peran=Peran.ADMIN)
    token = await _masuk(client, email)
    return admin, {"Authorization": f"Bearer {token}"}


def _tanggal_besok_wib(hari_tambah: int = 1) -> date:
    return datetime.now(TZ_WIB).date() + timedelta(days=hari_tambah)


async def test_daftar_akun_pengajar_kosong_dan_tidak_menampilkan_admin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    await _buat_pengguna(
        db_session, nama="Admin Kedua", email="admin2@contoh.id", peran=Peran.ADMIN
    )

    response = await client.get("/api/admin/akun-pengajar", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


async def test_daftar_akun_pengajar_tanpa_token_401(client: AsyncClient) -> None:
    response = await client.get("/api/admin/akun-pengajar")

    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_daftar_akun_pengajar_urut_terbaru_jumlah_batch_dan_status_efektif(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    sekarang = datetime.now(UTC)

    p_lama = await _buat_pengguna(
        db_session,
        nama="Sari Lestari",
        email="sari@contoh.id",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang + timedelta(days=30),
        dibuat_pada=sekarang - timedelta(days=10),
    )
    p_kadaluarsa = await _buat_pengguna(
        db_session,
        nama="Budi Santoso",
        email="budi@contoh.id",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang - timedelta(minutes=5),
        dibuat_pada=sekarang - timedelta(days=5),
    )
    await _buat_pengguna(
        db_session,
        nama="Dewi Anggraini",
        email="dewi@contoh.id",
        dinonaktifkan_pada=sekarang - timedelta(days=1),
        dibuat_pada=sekarang - timedelta(days=1),
    )

    db_session.add_all(
        [
            Batch(id_pengguna=p_lama.id_pengguna, nama_batch="B1", status=StatusBatch.AKTIF),
            Batch(id_pengguna=p_lama.id_pengguna, nama_batch="B2", status=StatusBatch.SELESAI),
            Batch(id_pengguna=p_kadaluarsa.id_pengguna, nama_batch="B3", status=StatusBatch.AKTIF),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/admin/akun-pengajar", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["email"] for item in body] == [
        "dewi@contoh.id",
        "budi@contoh.id",
        "sari@contoh.id",
    ]
    assert body[0]["dinonaktifkan_pada"] is not None
    assert body[0]["jumlah_batch"] == 0
    assert body[0]["status_langganan"] == "free"

    # Pro yang sudah kedaluwarsa harus tampil sebagai free dengan masa_berlaku_pro None.
    assert body[1]["status_langganan"] == "free"
    assert body[1]["masa_berlaku_pro"] is None
    assert body[1]["jumlah_batch"] == 1

    assert body[2]["status_langganan"] == "pro"
    assert body[2]["masa_berlaku_pro"] is not None
    assert body[2]["jumlah_batch"] == 2


async def test_daftar_akun_pengajar_cari_dan_filter(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    sekarang = datetime.now(UTC)

    await _buat_pengguna(
        db_session,
        nama="Sari Lestari",
        email="sari@contoh.id",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang + timedelta(days=15),
    )
    await _buat_pengguna(
        db_session,
        nama="Budi Santoso",
        email="budi_50%@contoh.id",
        status_langganan=StatusLangganan.PRO,
        masa_berlaku_pro=sekarang - timedelta(hours=1),
    )
    await _buat_pengguna(
        db_session,
        nama="Dewi Anggraini",
        email="dewi@contoh.id",
        status_langganan=StatusLangganan.FREE,
        dinonaktifkan_pada=sekarang,
    )

    # Cari nama (case-insensitive + trim)
    resp = await client.get(
        "/api/admin/akun-pengajar", params={"cari": "  sari  "}, headers=headers
    )
    assert resp.status_code == 200
    assert [item["email"] for item in resp.json()] == ["sari@contoh.id"]

    # Cari email dengan wildcard % dan _ literal (tidak boleh cocok semua akun)
    resp = await client.get("/api/admin/akun-pengajar", params={"cari": "50%"}, headers=headers)
    assert resp.status_code == 200
    assert [item["email"] for item in resp.json()] == ["budi_50%@contoh.id"]

    resp = await client.get("/api/admin/akun-pengajar", params={"cari": "_50"}, headers=headers)
    assert resp.status_code == 200
    assert [item["email"] for item in resp.json()] == ["budi_50%@contoh.id"]

    # Filter status_langganan memakai efektif (Pro kedaluwarsa masuk free, bukan pro)
    resp_pro = await client.get(
        "/api/admin/akun-pengajar", params={"status_langganan": "pro"}, headers=headers
    )
    assert [item["email"] for item in resp_pro.json()] == ["sari@contoh.id"]

    resp_free = await client.get(
        "/api/admin/akun-pengajar", params={"status_langganan": "free"}, headers=headers
    )
    assert {item["email"] for item in resp_free.json()} == {
        "budi_50%@contoh.id",
        "dewi@contoh.id",
    }

    # Filter status_akun
    resp_nonaktif = await client.get(
        "/api/admin/akun-pengajar", params={"status_akun": "nonaktif"}, headers=headers
    )
    assert [item["email"] for item in resp_nonaktif.json()] == ["dewi@contoh.id"]

    # Kombinasi cari + status_langganan + status_akun
    resp_kombinasi = await client.get(
        "/api/admin/akun-pengajar",
        params={"cari": "contoh.id", "status_langganan": "free", "status_akun": "aktif"},
        headers=headers,
    )
    assert [item["email"] for item in resp_kombinasi.json()] == ["budi_50%@contoh.id"]


async def test_daftar_akun_pengajar_query_tidak_valid_422(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)

    r1 = await client.get(
        "/api/admin/akun-pengajar", params={"status_langganan": "vip"}, headers=headers
    )
    assert r1.status_code == 422
    assert r1.json()["kode"] == "VALIDASI_GAGAL"

    r2 = await client.get(
        "/api/admin/akun-pengajar", params={"status_akun": "diblokir"}, headers=headers
    )
    assert r2.status_code == 422
    assert r2.json()["kode"] == "VALIDASI_GAGAL"


async def test_ubah_langganan_free_ke_pro_inklusif_2359_wib_dan_kembali_ke_free(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    pengajar = await _buat_pengguna(db_session, nama="Budi", email="budi@contoh.id")
    tanggal_target = _tanggal_besok_wib(10)

    resp_pro = await client.patch(
        f"/api/admin/akun-pengajar/{pengajar.id_pengguna}/langganan",
        json={"status_langganan": "pro", "masa_berlaku_pro": tanggal_target.isoformat()},
        headers=headers,
    )

    assert resp_pro.status_code == 200
    body_pro = resp_pro.json()
    assert body_pro["status_langganan"] == "pro"
    assert body_pro["masa_berlaku_pro"] is not None

    await db_session.refresh(pengajar)
    batas_diharapkan = datetime(
        tanggal_target.year, tanggal_target.month, tanggal_target.day, 23, 59, 59, tzinfo=TZ_WIB
    )
    assert pengajar.masa_berlaku_pro == batas_diharapkan

    # Inklusif pada 23:59 WIB, berakhir pada 00:00 WIB keesokan harinya.
    pada_2359_wib = datetime(
        tanggal_target.year, tanggal_target.month, tanggal_target.day, 23, 59, 0, tzinfo=TZ_WIB
    )
    esok_0000_wib = datetime(
        tanggal_target.year, tanggal_target.month, tanggal_target.day, 0, 0, 0, tzinfo=TZ_WIB
    ) + timedelta(days=1)
    assert jenis_akun_efektif(pengajar, sekarang=pada_2359_wib) is StatusLangganan.PRO
    assert jenis_akun_efektif(pengajar, sekarang=esok_0000_wib) is StatusLangganan.FREE

    # Ubah kembali ke Free: masa_berlaku_pro dikosongkan.
    resp_free = await client.patch(
        f"/api/admin/akun-pengajar/{pengajar.id_pengguna}/langganan",
        json={"status_langganan": "free", "masa_berlaku_pro": tanggal_target.isoformat()},
        headers=headers,
    )
    assert resp_free.status_code == 200
    assert resp_free.json()["status_langganan"] == "free"
    assert resp_free.json()["masa_berlaku_pro"] is None

    await db_session.refresh(pengajar)
    assert pengajar.status_langganan is StatusLangganan.FREE
    assert pengajar.masa_berlaku_pro is None


@pytest.mark.parametrize(
    "masa_berlaku",
    [
        None,
        "",
        "   ",
        "bukan-tanggal",
        "2026-02-30",
        "2026-11-30T23:59:59Z",
        12345,
        True,
    ],
)
async def test_ubah_langganan_pro_masa_berlaku_tidak_valid_ditolak(
    client: AsyncClient, db_session: AsyncSession, masa_berlaku
) -> None:
    _, headers = await _token_admin(client, db_session)
    pengajar = await _buat_pengguna(db_session, nama="Budi", email="budi@contoh.id")

    response = await client.patch(
        f"/api/admin/akun-pengajar/{pengajar.id_pengguna}/langganan",
        json={"status_langganan": "pro", "masa_berlaku_pro": masa_berlaku},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "kode": "MASA_BERLAKU_TIDAK_VALID",
        "pesan": "Masa berlaku wajib diisi dengan tanggal setelah hari ini.",
    }


async def test_ubah_langganan_pro_hari_ini_dan_masa_lalu_wib_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    pengajar = await _buat_pengguna(db_session, nama="Budi", email="budi@contoh.id")
    hari_ini = datetime.now(TZ_WIB).date()
    kemarin = hari_ini - timedelta(days=1)

    for tanggal in (hari_ini, kemarin):
        response = await client.patch(
            f"/api/admin/akun-pengajar/{pengajar.id_pengguna}/langganan",
            json={"status_langganan": "pro", "masa_berlaku_pro": tanggal.isoformat()},
            headers=headers,
        )
        assert response.status_code == 400
        assert response.json()["kode"] == "MASA_BERLAKU_TIDAK_VALID"


async def test_nonaktifkan_mencabut_semua_sesi_tanpa_hapus_data_dan_aktifkan_kembali(
    client: AsyncClient,
    db_session: AsyncSession,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    _, headers_admin = await _token_admin(client, db_session)
    pengajar = await _buat_pengguna(db_session, nama="Budi", email="budi@contoh.id")
    id_pengajar = pengajar.id_pengguna

    # Buat 1 batch milik Pengajar dan 2 sesi aktif (multi-perangkat) + 1 token reset.
    token_1 = await _masuk(client, "budi@contoh.id")
    cookie_1 = client.cookies.get("refresh_token")
    token_2 = await _masuk(client, "budi@contoh.id")
    cookie_2 = client.cookies.get("refresh_token")

    resp_batch = await client.post(
        "/api/batch",
        json={"nama_batch": "UTS Kelas X"},
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert resp_batch.status_code == 201
    id_batch = resp_batch.json()["id_batch"]

    await client.post("/api/auth/lupa-password", json={"email": "budi@contoh.id"})
    _, reset_args, _ = _background_tasks_tidak_dijalankan[0]
    token_reset = reset_args[1]

    # Admin menonaktifkan akun Pengajar.
    resp_nonaktif = await client.post(
        f"/api/admin/akun-pengajar/{id_pengajar}/nonaktifkan",
        headers=headers_admin,
    )
    assert resp_nonaktif.status_code == 200
    assert resp_nonaktif.json()["dinonaktifkan_pada"] is not None
    assert resp_nonaktif.json()["jumlah_batch"] == 1

    # Semua sesi akun tersebut dicabut.
    sesi_list = list(await db_session.scalars(select(Sesi).where(Sesi.id_pengguna == id_pengajar)))
    assert len(sesi_list) == 2
    assert all(s.dicabut_pada is not None for s in sesi_list)

    # Kedua access token langsung ditolak pada request terproteksi.
    for tok in (token_1, token_2):
        r = await client.get("/api/auth/saya", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401
        assert r.json()["kode"] == "SESI_BERAKHIR"

    # Kedua refresh token ditolak.
    for ck in (cookie_1, cookie_2):
        client.cookies.set("refresh_token", ck)
        r = await client.post("/api/auth/refresh")
        assert r.status_code == 401
        assert r.json()["kode"] == "SESI_BERAKHIR"

    # Login ditolak dengan pesan generik.
    r_login = await client.post(
        "/api/auth/masuk", json={"email": "budi@contoh.id", "password": "rahasia123"}
    )
    assert r_login.status_code == 401
    assert r_login.json() == {"kode": "LOGIN_GAGAL", "pesan": "Email atau password salah"}

    # Atur ulang password dengan token sebelumnya ditolak.
    r_reset = await client.post(
        "/api/auth/atur-ulang-password",
        json={"token": token_reset, "password_baru": "baru12345"},
    )
    assert r_reset.status_code == 400
    assert r_reset.json()["kode"] == "TOKEN_RESET_TIDAK_VALID"

    # Data akun dan batch tetap ada di database.
    batch_db = await db_session.scalar(select(Batch).where(Batch.id_batch == uuid.UUID(id_batch)))
    assert batch_db is not None

    # Idempoten saat dinonaktifkan lagi.
    resp_nonaktif_ulang = await client.post(
        f"/api/admin/akun-pengajar/{id_pengajar}/nonaktifkan",
        headers=headers_admin,
    )
    assert resp_nonaktif_ulang.status_code == 200
    assert resp_nonaktif_ulang.json()["dinonaktifkan_pada"] is not None

    # Admin mengaktifkan kembali akun.
    resp_aktif = await client.post(
        f"/api/admin/akun-pengajar/{id_pengajar}/aktifkan",
        headers=headers_admin,
    )
    assert resp_aktif.status_code == 200
    assert resp_aktif.json()["dinonaktifkan_pada"] is None

    # Sesi lama tetap dicabut, tetapi login baru berhasil dan data batch lama utuh.
    r_lama = await client.get("/api/auth/saya", headers={"Authorization": f"Bearer {token_1}"})
    assert r_lama.status_code == 401

    token_baru = await _masuk(client, "budi@contoh.id")
    r_batch_lagi = await client.get(
        f"/api/batch/{id_batch}", headers={"Authorization": f"Bearer {token_baru}"}
    )
    assert r_batch_lagi.status_code == 200
    assert r_batch_lagi.json()["nama_batch"] == "UTS Kelas X"


async def test_target_tidak_ada_atau_target_admin_mengembalikan_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin, headers = await _token_admin(client, db_session)
    id_acak = uuid.uuid4()
    besok = _tanggal_besok_wib().isoformat()

    for target_id in (id_acak, admin.id_pengguna):
        r1 = await client.patch(
            f"/api/admin/akun-pengajar/{target_id}/langganan",
            json={"status_langganan": "pro", "masa_berlaku_pro": besok},
            headers=headers,
        )
        assert r1.status_code == 404
        assert r1.json()["kode"] == "AKUN_TIDAK_DITEMUKAN"

        r2 = await client.post(f"/api/admin/akun-pengajar/{target_id}/nonaktifkan", headers=headers)
        assert r2.status_code == 404
        assert r2.json()["kode"] == "AKUN_TIDAK_DITEMUKAN"

        r3 = await client.post(f"/api/admin/akun-pengajar/{target_id}/aktifkan", headers=headers)
        assert r3.status_code == 404
        assert r3.json()["kode"] == "AKUN_TIDAK_DITEMUKAN"


@pytest.mark.parametrize(
    "method,suffix,body",
    [
        ("PATCH", "langganan", {"status_langganan": "free"}),
        ("POST", "nonaktifkan", None),
        ("POST", "aktifkan", None),
    ],
)
async def test_id_pengguna_bukan_uuid_mengembalikan_422_validasi_gagal(
    client: AsyncClient,
    db_session: AsyncSession,
    method: str,
    suffix: str,
    body: dict | None,
) -> None:
    _, headers = await _token_admin(client, db_session)
    url = f"/api/admin/akun-pengajar/bukan-uuid/{suffix}"

    if method == "PATCH":
        response = await client.patch(url, json=body, headers=headers)
    else:
        response = await client.post(url, headers=headers)

    assert response.status_code == 422
    assert response.json() == {"kode": "VALIDASI_GAGAL", "pesan": "Data yang dikirim tidak valid."}


async def test_gagal_commit_langganan_dan_status_akun_mengembalikan_500(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, headers = await _token_admin(client, db_session)
    pengajar = await _buat_pengguna(db_session, nama="Budi", email="budi@contoh.id")
    id_pengajar = pengajar.id_pengguna

    with patch.object(db_session, "commit", AsyncMock(side_effect=SQLAlchemyError("db fail"))):
        r_langganan = await client.patch(
            f"/api/admin/akun-pengajar/{id_pengajar}/langganan",
            json={"status_langganan": "free"},
            headers=headers,
        )
        assert r_langganan.status_code == 500
        assert r_langganan.json() == {
            "kode": "GAGAL_UBAH_LANGGANAN",
            "pesan": "Gagal mengubah status langganan, silakan coba lagi.",
        }

        r_nonaktif = await client.post(
            f"/api/admin/akun-pengajar/{id_pengajar}/nonaktifkan",
            headers=headers,
        )
        assert r_nonaktif.status_code == 500
        assert r_nonaktif.json() == {
            "kode": "GAGAL_UBAH_STATUS_AKUN",
            "pesan": "Gagal mengubah status akun, silakan coba lagi.",
        }

        r_aktif = await client.post(
            f"/api/admin/akun-pengajar/{id_pengajar}/aktifkan",
            headers=headers,
        )
        assert r_aktif.status_code == 500
        assert r_aktif.json() == {
            "kode": "GAGAL_UBAH_STATUS_AKUN",
            "pesan": "Gagal mengubah status akun, silakan coba lagi.",
        }
