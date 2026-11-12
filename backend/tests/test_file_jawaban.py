import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from httpx import AsyncClient
from pypdf import PdfWriter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.enums import StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.services import pemrosesan

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
        ("files", (nama_file, konten, content_type)) for nama_file, konten, content_type in daftar
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

    response = await client.post(f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token))
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
        "file_bermasalah": [{"indeks": 0, "kode": "FORMAT_FILE_TIDAK_DIDUKUNG"}],
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
        "file_bermasalah": [{"indeks": 0, "kode": "FILE_TERLALU_BESAR"}],
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
        "file_bermasalah": [{"indeks": 0, "kode": "PDF_TERLALU_BANYAK_HALAMAN"}],
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
        "file_bermasalah": [{"indeks": 0, "kode": "PDF_TIDAK_DAPAT_DIBACA"}],
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
        "file_bermasalah": [{"indeks": 0, "kode": "PDF_TIDAK_DAPAT_DIBACA"}],
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
    assert response.json()["file_bermasalah"] == [
        {"indeks": 1, "kode": "FORMAT_FILE_TIDAK_DIDUKUNG"}
    ]

    jumlah_baris = await db_session.scalar(
        select(FileJawaban).where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert jumlah_baris is None
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_unggah_jawaban_beberapa_file_bermasalah(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    konten_besar = _PNG + (b"0" * (10 * 1024 * 1024 + 1))
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(
            [
                ("a.png", _PNG, "image/png"),
                ("b.png", konten_besar, "image/png"),
                ("c.png", b"bukan png", "image/png"),
                ("d.pdf", _pdf_korup(), "application/pdf"),
            ]
        ),
        data=_nama("Budi", "Ani", "Citra", "Dedi"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    body = response.json()
    assert body["kode"] == "FILE_TERLALU_BESAR"
    assert body["pesan"] == "Ukuran file maksimal 10 MB."
    assert body["file_bermasalah"] == [
        {"indeks": 1, "kode": "FILE_TERLALU_BESAR"},
        {"indeks": 2, "kode": "FORMAT_FILE_TIDAK_DIDUKUNG"},
        {"indeks": 3, "kode": "PDF_TIDAK_DAPAT_DIBACA"},
    ]

    jumlah_baris = await db_session.scalar(
        select(FileJawaban).where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert jumlah_baris is None
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_unggah_jawaban_satu_bermasalah_di_tengah_file_valid(
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
                ("c.png", _PNG, "image/png"),
            ]
        ),
        data=_nama("Budi", "Ani", "Citra"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    body = response.json()
    assert body["kode"] == "FORMAT_FILE_TIDAK_DIDUKUNG"
    assert body["file_bermasalah"] == [{"indeks": 1, "kode": "FORMAT_FILE_TIDAK_DIDUKUNG"}]

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


async def test_unggah_jawaban_menjadwalkan_pemrosesan(
    client: AsyncClient, _background_tasks_tidak_dijalankan: list[tuple]
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("a.png", _PNG, "image/png")]),
        data=_nama("Budi"),
        headers=_auth(token),
    )
    id_file = uuid.UUID(response.json()[0]["id_file"])

    assert len(_background_tasks_tidak_dijalankan) == 1
    func_task, args, kwargs = _background_tasks_tidak_dijalankan[0]
    assert func_task is pemrosesan.proses_file_jawaban
    assert args == ([id_file],)
    assert kwargs == {}


async def _set_langganan(
    db_session: AsyncSession,
    email: str,
    status: StatusLangganan,
    masa_berlaku_pro: datetime | None = None,
) -> None:
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == email))
    pengguna.status_langganan = status
    pengguna.masa_berlaku_pro = masa_berlaku_pro
    await db_session.commit()


async def _isi_file_jawaban_awal(
    db_session: AsyncSession,
    id_batch: str,
    jumlah: int,
) -> None:
    status_siklus = (StatusProses.DIPROSES, StatusProses.SELESAI, StatusProses.GAGAL)
    db_session.add_all(
        [
            FileJawaban(
                id_batch=uuid.UUID(id_batch),
                nama_peserta_didik=f"Peserta Awal {i + 1}",
                path=f"uploads/{id_batch}/awal-{i + 1}.png",
                status_proses=status_siklus[i % len(status_siklus)],
            )
            for i in range(jumlah)
        ]
    )
    await db_session.commit()


async def test_unggah_jawaban_akun_free_tepat_batas_15_sukses_dan_ke_16_ditolak(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    # 10 file dengan berbagai status_proses (diproses, selesai, gagal) tetap dihitung 1 per file.
    await _isi_file_jawaban_awal(db_session, id_batch, 10)

    # Unggah 5 file lagi: tepat mencapai batas 15 jawaban.
    daftar_5 = [(f"{i}.png", _PNG, "image/png") for i in range(5)]
    res_15 = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(daftar_5),
        data=_nama(*[f"Peserta Baru {i}" for i in range(5)]),
        headers=_auth(token),
    )
    assert res_15.status_code == 201

    total = await db_session.scalar(
        select(func.count())
        .select_from(FileJawaban)
        .where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert total == 15

    # Unggah ke-16 ditolak dengan sisa 0 slot.
    res_16 = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("16.png", _PNG, "image/png")]),
        data=_nama("Peserta 16"),
        headers=_auth(token),
    )
    assert res_16.status_code == 400
    assert res_16.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 0 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }


async def test_unggah_jawaban_akun_free_melebihi_sisa_slot_ditolak_seluruhnya(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 12)

    # Tersisa 3 slot, tetapi mengunggah 4 file sekaligus: harus ditolak seluruhnya.
    daftar_4 = [(f"{i}.png", _PNG, "image/png") for i in range(4)]
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(daftar_4),
        data=_nama("P1", "P2", "P3", "P4"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 3 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }

    total = await db_session.scalar(
        select(func.count())
        .select_from(FileJawaban)
        .where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert total == 12
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_unggah_jawaban_akun_pro_tepat_batas_50_sukses_dan_melebihi_sisa_slot_ditolak(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) + timedelta(days=30),
    )
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 48)

    # Sisa 2 slot: unggah 3 file ditolak seluruhnya dengan pesan Pro.
    daftar_3 = [(f"{i}.png", _PNG, "image/png") for i in range(3)]
    res_tolak = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(daftar_3),
        data=_nama("P1", "P2", "P3"),
        headers=_auth(token),
    )
    assert res_tolak.status_code == 400
    assert res_tolak.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Pro adalah 50, tersisa 2 slot. Kurangi jumlah file."
        ),
    }
    assert not any(p.is_file() for p in tmp_path.rglob("*"))

    # Unggah 2 file: tepat 50, sukses.
    daftar_2 = [(f"{i}.png", _PNG, "image/png") for i in range(2)]
    res_sukses = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(daftar_2),
        data=_nama("P49", "P50"),
        headers=_auth(token),
    )
    assert res_sukses.status_code == 201

    total = await db_session.scalar(
        select(func.count())
        .select_from(FileJawaban)
        .where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert total == 50

    # Unggah ke-51 ditolak dengan sisa 0 slot.
    res_51 = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("51.png", _PNG, "image/png")]),
        data=_nama("P51"),
        headers=_auth(token),
    )
    assert res_51.status_code == 400
    assert res_51.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Pro adalah 50, tersisa 0 slot. Kurangi jumlah file."
        ),
    }


async def test_unggah_jawaban_akun_pro_kedaluwarsa_di_atas_batas_free_ditolak_data_lama_utuh(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) - timedelta(seconds=1),
    )
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 20)

    # Data lama (20 file) tetap dapat dibaca.
    daftar = await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token))
    assert daftar.status_code == 200
    assert len(daftar.json()) == 20

    # Unggahan baru ditolak dengan batas Free dan tersisa 0 slot (bukan negatif).
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("baru.png", _PNG, "image/png")]),
        data=_nama("Peserta Baru"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 0 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }


async def test_unggah_jawaban_format_tidak_didukung_dan_melebihi_batas_prioritaskan_batas(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 15)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files([("rusak.png", b"bukan png valid", "image/png")]),
        data=_nama("Peserta 16"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 0 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_unggah_jawaban_melebihi_batas_ditolak_tanpa_membaca_isi_file(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
) -> None:
    from app.services import file_jawaban as layanan_file_jawaban

    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 14)

    dipanggil = False

    async def _jangan_baca_file(*_args, **_kwargs):
        nonlocal dipanggil
        dipanggil = True
        raise AssertionError("baca_dan_validasi_file tidak boleh dipanggil saat melebihi batas")

    monkeypatch.setattr(layanan_file_jawaban, "baca_dan_validasi_file", _jangan_baca_file)

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=_files(
            [
                ("rusak1.png", b"isi tidak valid 1", "image/png"),
                ("rusak2.pdf", _pdf_korup(), "application/pdf"),
            ]
        ),
        data=_nama("Peserta 15", "Peserta 16"),
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 1 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }
    assert dipanggil is False
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_balapan_unggah_jawaban_pada_sisa_slot_hanya_satu_lolos(
    client: AsyncClient, db_session: AsyncSession, _engine, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _isi_file_jawaban_awal(db_session, id_batch, 13)

    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async def _get_db_per_request() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as sesi:
            yield sesi

    override_lama = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db_per_request
    try:
        r1, r2 = await asyncio.gather(
            client.post(
                f"/api/batch/{id_batch}/file-jawaban",
                files=_files([("a1.png", _PNG, "image/png"), ("a2.png", _PNG, "image/png")]),
                data=_nama("A1", "A2"),
                headers=_auth(token),
            ),
            client.post(
                f"/api/batch/{id_batch}/file-jawaban",
                files=_files([("b1.png", _PNG, "image/png"), ("b2.png", _PNG, "image/png")]),
                data=_nama("B1", "B2"),
                headers=_auth(token),
            ),
        )
    finally:
        if override_lama is not None:
            app.dependency_overrides[get_db] = override_lama
        else:
            app.dependency_overrides.pop(get_db, None)

    assert sorted([r1.status_code, r2.status_code]) == [201, 400]
    gagal = r1 if r1.status_code == 400 else r2
    assert gagal.json() == {
        "kode": "BATAS_JAWABAN_TERLAMPAUI",
        "pesan": (
            "Upload ditolak: batas jawaban akun Free adalah 15, tersisa 0 slot. "
            "Kurangi jumlah file atau upgrade ke Pro."
        ),
    }

    total = await db_session.scalar(
        select(func.count())
        .select_from(FileJawaban)
        .where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert total == 15
