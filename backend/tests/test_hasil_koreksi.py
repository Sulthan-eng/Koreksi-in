import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Kategori, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _buat_batch(client: AsyncClient, token: str, nama_batch: str = "Batch") -> str:
    buat = await client.post("/api/batch", json={"nama_batch": nama_batch}, headers=_auth(token))
    return buat.json()["id_batch"]


async def _tambah_soal(client: AsyncClient, token: str, id_batch: str, kunci: str = "Kunci") -> str:
    soal = await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": kunci}, headers=_auth(token)
    )
    return soal.json()["id_soal"]


async def _buat_file_jawaban(
    db_session: AsyncSession,
    id_batch: str,
    nama_peserta_didik: str,
    status_proses: StatusProses,
    diunggah_pada=None,
) -> FileJawaban:
    file_jawaban = FileJawaban(
        id_batch=uuid.UUID(id_batch),
        nama_peserta_didik=nama_peserta_didik,
        path=f"uploads/{id_batch}/contoh.pdf",
        status_proses=status_proses,
        **({"diunggah_pada": diunggah_pada} if diunggah_pada else {}),
    )
    db_session.add(file_jawaban)
    await db_session.commit()
    return file_jawaban


async def _buat_hasil_koreksi(
    db_session: AsyncSession,
    id_file: uuid.UUID,
    id_soal: str,
    teks_ocr: str = "Jawaban peserta didik",
    skor_sistem: int = 85,
    kategori: Kategori = Kategori.SANGAT_MIRIP,
) -> None:
    db_session.add(
        HasilKoreksi(
            id_file=id_file,
            id_soal=uuid.UUID(id_soal),
            teks_ocr=teks_ocr,
            skor_sistem=skor_sistem,
            kategori=kategori,
        )
    )
    await db_session.commit()


async def test_daftar_hasil_koreksi_hanya_selesai(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    id_soal = await _tambah_soal(client, token, id_batch)

    file_selesai = await _buat_file_jawaban(db_session, id_batch, "Budi", StatusProses.SELESAI)
    await _buat_hasil_koreksi(db_session, file_selesai.id_file, id_soal)

    file_diproses = await _buat_file_jawaban(db_session, id_batch, "Ani", StatusProses.DIPROSES)
    await _buat_hasil_koreksi(db_session, file_diproses.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/hasil", headers=_auth(token))
    assert response.status_code == 200
    daftar = response.json()
    assert len(daftar) == 1
    assert daftar[0]["nama_peserta_didik"] == "Budi"
    assert daftar[0]["no_soal"] == 1
    assert daftar[0]["teks_ocr"] == "Jawaban peserta didik"
    assert daftar[0]["skor_sistem"] == 85
    assert daftar[0]["kategori"] == "sangat_mirip"


async def test_daftar_hasil_koreksi_urutan(client: AsyncClient, db_session: AsyncSession) -> None:
    from datetime import UTC, datetime, timedelta

    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    id_soal_1 = await _tambah_soal(client, token, id_batch, "Kunci 1")
    id_soal_2 = await _tambah_soal(client, token, id_batch, "Kunci 2")

    basis = datetime.now(UTC)
    file_kedua = await _buat_file_jawaban(
        db_session, id_batch, "Diunggah Kedua", StatusProses.SELESAI, basis + timedelta(seconds=1)
    )
    file_pertama = await _buat_file_jawaban(
        db_session, id_batch, "Diunggah Pertama", StatusProses.SELESAI, basis
    )

    await _buat_hasil_koreksi(db_session, file_kedua.id_file, id_soal_2)
    await _buat_hasil_koreksi(db_session, file_kedua.id_file, id_soal_1)
    await _buat_hasil_koreksi(db_session, file_pertama.id_file, id_soal_2)
    await _buat_hasil_koreksi(db_session, file_pertama.id_file, id_soal_1)

    response = await client.get(f"/api/batch/{id_batch}/hasil", headers=_auth(token))
    assert response.status_code == 200
    daftar = response.json()
    urutan = [(item["nama_peserta_didik"], item["no_soal"]) for item in daftar]
    assert urutan == [
        ("Diunggah Pertama", 1),
        ("Diunggah Pertama", 2),
        ("Diunggah Kedua", 1),
        ("Diunggah Kedua", 2),
    ]


async def test_daftar_hasil_koreksi_isolasi_batch(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")
    id_batch = await _buat_batch(client, token_a)
    id_soal = await _tambah_soal(client, token_a, id_batch)
    file_selesai = await _buat_file_jawaban(db_session, id_batch, "Budi", StatusProses.SELESAI)
    await _buat_hasil_koreksi(db_session, file_selesai.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/hasil", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_daftar_hasil_koreksi_id_batch_acak(client: AsyncClient) -> None:
    token = await _token(client)
    response = await client.get(f"/api/batch/{uuid.uuid4()}/hasil", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_daftar_hasil_koreksi_tanpa_token(client: AsyncClient) -> None:
    response = await client.get(f"/api/batch/{uuid.uuid4()}/hasil")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"
