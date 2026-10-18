import os
import uuid
from io import BytesIO

import pytest
from httpx import AsyncClient
from pypdf import PdfWriter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.file_jawaban import FileJawaban

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}

_PNG = b"\x89PNG\r\n\x1a\n" + b"konten png palsu"
_JPEG = b"\xff\xd8\xff" + b"konten jpeg palsu"


def _pdf(jumlah_halaman: int) -> bytes:
    writer = PdfWriter()
    for _ in range(jumlah_halaman):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _pdf_korup() -> bytes:
    return b"%PDF-1.4\n" + os.urandom(100)


def _pdf_terpotong() -> bytes:
    utuh = _pdf(1)
    return utuh[: len(utuh) // 2]


async def _daftar_dan_masuk(client: AsyncClient, email: str = "budi@contoh.com") -> dict:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    hasil = await _daftar_dan_masuk(client, email)
    return hasil["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _buat_batch_dengan_soal(client: AsyncClient, token: str) -> str:
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]
    await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Kunci"}, headers=_auth(token)
    )
    return id_batch


@pytest.fixture(autouse=True)
def _upload_dir_sementara(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


def _files(daftar: list[tuple[str, bytes, str]]) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [
        ("files", (nama_file, konten, content_type))
        for nama_file, konten, content_type in daftar
    ]


def _nama(*nama_list: str) -> dict[str, list[str]]:
    return {"nama_peserta_didik": list(nama_list)}


async def test_unggah_jawaban_sukses(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("  Budi  "),
        headers=_auth(token),
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["nama_peserta_didik"] == "Budi"
    assert body[0]["status_proses"] == "diproses"
    assert body[0]["pesan_error"] is None

    baris = await db_session.scalar(
        select(FileJawaban).where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert baris is not None
    assert baris.nama_peserta_didik == "Budi"
    assert baris.path.startswith(f"uploads/{id_batch}/")
    assert (tmp_path / baris.path).exists()

    response = await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token))
    assert response.status_code == 200
    daftar = response.json()
    assert len(daftar) == 1
    assert daftar[0]["nama_peserta_didik"] == "Budi"


async def test_unggah_jawaban_belum_ada_soal(client: AsyncClient) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BELUM_ADA_SOAL",
        "pesan": "Tambahkan minimal satu soal sebelum mengunggah jawaban.",
    }


async def test_unggah_jawaban_tanpa_file(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "TIDAK_ADA_FILE",
        "pesan": "Pilih minimal satu file untuk diunggah.",
    }


async def test_unggah_jawaban_lebih_dari_10_file(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    daftar_file = [(f"{i}.png", _PNG, "image/png") for i in range(11)]
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(daftar_file),
        data=_nama(*[f"Peserta {i}" for i in range(11)]),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "MAKS_FILE_TERLAMPAUI",
        "pesan": "Maksimal 10 file per unggahan.",
    }


async def test_unggah_jawaban_nama_kosong(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("   "),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "NAMA_PESERTA_KOSONG",
        "pesan": "Nama peserta didik wajib untuk semua file",
    }


async def test_unggah_jawaban_nama_terlalu_panjang(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("a" * 101),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "NAMA_PESERTA_TERLALU_PANJANG",
        "pesan": "Nama peserta didik maksimal 100 karakter.",
    }


async def test_unggah_jawaban_format_tidak_didukung(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", b"ini bukan png sama sekali", "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "FORMAT_FILE_TIDAK_DIDUKUNG",
        "pesan": "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
    }


async def test_unggah_jawaban_file_terlalu_besar(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    konten_besar = _PNG + (b"0" * (10 * 1024 * 1024 + 1))
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", konten_besar, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "FILE_TERLALU_BESAR",
        "pesan": "Ukuran file maksimal 10 MB.",
    }


async def test_unggah_jawaban_pdf_terlalu_banyak_halaman(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.pdf", _pdf(16), "application/pdf")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "PDF_TERLALU_BANYAK_HALAMAN",
        "pesan": "PDF maksimal 15 halaman.",
    }


async def test_unggah_jawaban_pdf_korup(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.pdf", _pdf_korup(), "application/pdf")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "PDF_TIDAK_DAPAT_DIBACA",
        "pesan": "File PDF rusak atau tidak dapat dibaca.",
    }


async def test_unggah_jawaban_pdf_terpotong(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.pdf", _pdf_terpotong(), "application/pdf")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "PDF_TIDAK_DAPAT_DIBACA",
        "pesan": "File PDF rusak atau tidak dapat dibaca.",
    }


async def test_unggah_jawaban_all_or_nothing(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(
            [
                ("a.png", _PNG, "image/png"),
                ("b.png", b"bukan png", "image/png"),
            ]
        ),
        data=_nama("Budi", "Ani"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "FORMAT_FILE_TIDAK_DIDUKUNG"

    jumlah_baris = await db_session.scalar(
        select(FileJawaban).where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert jumlah_baris is None
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_unggah_jawaban_isolasi_batch(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")
    id_batch = await _buat_batch_dengan_soal(client, token_a)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token_b),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"

    response = await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_unggah_jawaban_id_batch_acak(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch_acak = uuid.uuid4()

    response = await client.post(
        f"/api/batch/{id_batch_acak}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_unggah_jawaban_tanpa_token(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/batch/{uuid.uuid4()}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
    )
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_daftar_file_jawaban_tanpa_token(client: AsyncClient) -> None:
    response = await client.get(f"/api/batch/{uuid.uuid4()}/file-jawaban")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_tambah_soal_setelah_unggah_jawaban_ditolak(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )

    response = await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Kunci lain"}, headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "SOAL_SETELAH_JAWABAN"
