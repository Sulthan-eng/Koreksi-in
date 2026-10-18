import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.soal import Soal

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}


async def _daftar_dan_masuk(client: AsyncClient, email: str = "budi@contoh.com") -> dict:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    hasil = await _daftar_dan_masuk(client, email)
    return hasil["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_buat_batch_dan_daftar_batch_sukses(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.post(
        "/api/batch", json={"nama_batch": "Ujian Tengah Semester"}, headers=_auth(token)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["nama_batch"] == "Ujian Tengah Semester"
    assert body["status"] == "aktif"

    response = await client.get("/api/batch", headers=_auth(token))
    assert response.status_code == 200
    daftar = response.json()
    assert len(daftar) == 1
    assert daftar[0]["id_batch"] == body["id_batch"]


async def test_daftar_batch_hanya_milik_sendiri(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")

    await client.post("/api/batch", json={"nama_batch": "Batch A"}, headers=_auth(token_a))
    await client.post("/api/batch", json={"nama_batch": "Batch B"}, headers=_auth(token_b))

    response = await client.get("/api/batch", headers=_auth(token_a))
    daftar = response.json()
    assert len(daftar) == 1
    assert daftar[0]["nama_batch"] == "Batch A"


async def test_daftar_batch_terbaru_dulu(client: AsyncClient) -> None:
    token = await _token(client)

    await client.post("/api/batch", json={"nama_batch": "Pertama"}, headers=_auth(token))
    await client.post("/api/batch", json={"nama_batch": "Kedua"}, headers=_auth(token))

    response = await client.get("/api/batch", headers=_auth(token))
    daftar = response.json()
    assert [b["nama_batch"] for b in daftar] == ["Kedua", "Pertama"]


async def test_ambil_batch_404_milik_pengguna_lain(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")

    buat = await client.post("/api/batch", json={"nama_batch": "Batch A"}, headers=_auth(token_a))
    id_batch = buat.json()["id_batch"]

    response = await client.get(f"/api/batch/{id_batch}", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json() == {"kode": "BATCH_TIDAK_DITEMUKAN", "pesan": "Batch tidak ditemukan"}


async def test_ambil_batch_404_id_acak(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.get(f"/api/batch/{uuid.uuid4()}", headers=_auth(token))
    assert response.status_code == 404
    assert response.json() == {"kode": "BATCH_TIDAK_DITEMUKAN", "pesan": "Batch tidak ditemukan"}


async def test_daftar_dan_tambah_soal_404_milik_pengguna_lain(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")

    buat = await client.post("/api/batch", json={"nama_batch": "Batch A"}, headers=_auth(token_a))
    id_batch = buat.json()["id_batch"]

    response = await client.get(f"/api/batch/{id_batch}/soal", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"

    response = await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Jawaban"}, headers=_auth(token_b)
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_daftar_dan_tambah_soal_404_id_batch_acak(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch_acak = uuid.uuid4()

    response = await client.get(f"/api/batch/{id_batch_acak}/soal", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"

    response = await client.post(
        f"/api/batch/{id_batch_acak}/soal",
        json={"kunci_jawaban": "Jawaban"},
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_buat_batch_nama_kosong(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.post("/api/batch", json={"nama_batch": ""}, headers=_auth(token))
    assert response.status_code == 400
    assert response.json() == {
        "kode": "NAMA_BATCH_KOSONG",
        "pesan": "Nama batch tidak boleh kosong.",
    }


async def test_buat_batch_nama_spasi_saja(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.post("/api/batch", json={"nama_batch": "   "}, headers=_auth(token))
    assert response.status_code == 400
    assert response.json()["kode"] == "NAMA_BATCH_KOSONG"


async def test_buat_batch_nama_kepanjangan(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.post("/api/batch", json={"nama_batch": "a" * 101}, headers=_auth(token))
    assert response.status_code == 422
    assert response.json()["kode"] == "VALIDASI_GAGAL"


async def test_tambah_soal_berurutan(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    for nomor in (1, 2, 3):
        response = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert response.status_code == 201
        assert response.json()["no_soal"] == nomor

    response = await client.get(f"/api/batch/{id_batch}/soal", headers=_auth(token))
    daftar = response.json()
    assert [s["no_soal"] for s in daftar] == [1, 2, 3]


async def test_tambah_soal_kunci_kosong(client: AsyncClient) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    response = await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": ""}, headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "KUNCI_KOSONG",
        "pesan": "Kunci jawaban tidak boleh kosong",
    }


async def test_tambah_soal_kunci_spasi_saja(client: AsyncClient) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    response = await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "   "}, headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "KUNCI_KOSONG"


async def test_tambah_soal_ke_21_ditolak(client: AsyncClient) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    for nomor in range(1, 21):
        response = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert response.status_code == 201

    response = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci ke-21"},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Maksimal 20 soal per batch.",
    }


async def test_tambah_soal_setelah_file_jawaban_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    db_session.add(
        FileJawaban(
            id_batch=id_batch,
            nama_peserta_didik="Peserta",
            path=f"uploads/{id_batch}/contoh.pdf",
            status_proses=StatusProses.DIPROSES,
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci"},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "SOAL_SETELAH_JAWABAN",
        "pesan": "Soal tidak dapat ditambah setelah jawaban diunggah.",
    }

    jumlah_soal = await db_session.scalar(select(Soal).where(Soal.id_batch == uuid.UUID(id_batch)))
    assert jumlah_soal is None


async def test_daftar_batch_tanpa_token(client: AsyncClient) -> None:
    response = await client.get("/api/batch")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_buat_batch_tanpa_token(client: AsyncClient) -> None:
    response = await client.post("/api/batch", json={"nama_batch": "Batch"})
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_ambil_batch_tanpa_token(client: AsyncClient) -> None:
    response = await client.get(f"/api/batch/{uuid.uuid4()}")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_daftar_soal_tanpa_token(client: AsyncClient) -> None:
    response = await client.get(f"/api/batch/{uuid.uuid4()}/soal")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_tambah_soal_tanpa_token(client: AsyncClient) -> None:
    response = await client.post(f"/api/batch/{uuid.uuid4()}/soal", json={"kunci_jawaban": "Kunci"})
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"
