import uuid
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from httpx import AsyncClient
from pypdf import PdfWriter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import gemini

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}
_PNG = b"\x89PNG\r\n\x1a\n" + b"konten png palsu"


@pytest.fixture(autouse=True)
def _upload_dir_sementara(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


def _pdf(jumlah_halaman: int) -> bytes:
    writer = PdfWriter()
    for _ in range(jumlah_halaman):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _buat_batch(client: AsyncClient, token: str) -> str:
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    return buat.json()["id_batch"]


def _mock_ocr_kunci(monkeypatch, teks: str | None = None, exc: Exception | None = None) -> None:
    async def fake_ocr_kunci(konten, ext):
        if exc is not None:
            raise exc
        return teks

    monkeypatch.setattr(gemini, "ocr_kunci", fake_ocr_kunci)


async def test_ocr_kunci_sukses(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="Teks kunci hasil OCR")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json() == {"teks": "Teks kunci hasil OCR"}

    jumlah_soal = await db_session.scalar(select(Soal).where(Soal.id_batch == uuid.UUID(id_batch)))
    assert jumlah_soal is None
    assert list(tmp_path.iterdir()) == []


async def test_ocr_kunci_hasil_kosong_dianggap_gagal(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="   ")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json() == {
        "kode": "OCR_KUNCI_GAGAL",
        "pesan": "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual",
    }


async def test_ocr_kunci_penanda_tidak_ada_teks_dianggap_gagal(
    client: AsyncClient, monkeypatch
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks=gemini.PENANDA_TIDAK_ADA_TEKS)

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json() == {
        "kode": "OCR_KUNCI_GAGAL",
        "pesan": "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual",
    }


async def test_ocr_kunci_penanda_tidak_ada_teks_dengan_spasi_sekitar_dianggap_gagal(
    client: AsyncClient, monkeypatch
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks=f"  \n{gemini.PENANDA_TIDAK_ADA_TEKS}\n  ")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json()["kode"] == "OCR_KUNCI_GAGAL"


async def test_ocr_kunci_teks_normal_tetap_sukses(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="Jawaban yang benar adalah fotosintesis.")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json() == {"teks": "Jawaban yang benar adalah fotosintesis."}


async def test_ocr_kunci_kuota_harian_habis(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, exc=gemini.KuotaHarianHabis())

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json()["kode"] == "OCR_KUNCI_GAGAL"


async def test_ocr_kunci_gangguan_sementara(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, exc=gemini.GagalSementara())

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json()["kode"] == "OCR_KUNCI_GAGAL"


async def test_ocr_kunci_gagal_permanen(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, exc=gemini.GagalPermanen())

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 500
    assert response.json()["kode"] == "OCR_KUNCI_GAGAL"


async def test_ocr_kunci_format_tidak_didukung(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.txt", b"bukan gambar atau pdf", "text/plain")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "FORMAT_FILE_TIDAK_DIDUKUNG"


async def test_ocr_kunci_file_terlalu_besar(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")
    konten_besar = _PNG + b"\x00" * (10 * 1024 * 1024)

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", konten_besar, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "FILE_TERLALU_BESAR"


async def test_ocr_kunci_pdf_terlalu_banyak_halaman(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.pdf", _pdf(16), "application/pdf")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "PDF_TERLALU_BANYAK_HALAMAN"


async def test_ocr_kunci_tanpa_file(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "TIDAK_ADA_FILE"


async def test_ocr_kunci_batch_selesai(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Kunci"}, headers=_auth(token)
    )
    await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "BATCH_SUDAH_SELESAI"


async def test_ocr_kunci_sudah_ada_jawaban(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    await client.post(
        f"/api/batch/{id_batch}/soal", json={"kunci_jawaban": "Kunci"}, headers=_auth(token)
    )
    db_session.add(
        FileJawaban(
            id_batch=uuid.UUID(id_batch),
            nama_peserta_didik="Peserta",
            path=f"uploads/{id_batch}/contoh.png",
            status_proses=StatusProses.DIPROSES,
        )
    )
    await db_session.commit()
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "SOAL_SETELAH_JAWABAN"


async def test_ocr_kunci_batas_soal_tercapai(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    for nomor in range(1, 16):
        response = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert response.status_code == 201
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 15 soal per batch.",
    }


async def test_ocr_kunci_akun_pro_batas_30_soal(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.status_langganan = StatusLangganan.PRO
    pengguna.masa_berlaku_pro = datetime.now(UTC) + timedelta(days=30)
    await db_session.commit()

    id_batch = await _buat_batch(client, token)
    db_session.add_all(
        [
            Soal(id_batch=uuid.UUID(id_batch), no_soal=nomor, kunci_jawaban=f"Kunci {nomor}")
            for nomor in range(1, 30)
        ]
    )
    await db_session.commit()
    _mock_ocr_kunci(monkeypatch, teks="Kunci soal ke-30")

    # Saat baru ada 29 soal, OCR kunci soal ke-30 masih diizinkan.
    res_ke_30 = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert res_ke_30.status_code == 200
    assert res_ke_30.json() == {"teks": "Kunci soal ke-30"}

    # Tambah soal ke-30, lalu OCR kunci berikutnya ditolak.
    await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci 30"},
        headers=_auth(token),
    )

    res_ke_31 = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert res_ke_31.status_code == 400
    assert res_ke_31.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 30 soal per batch.",
    }


async def test_ocr_kunci_akun_pro_kedaluwarsa_di_atas_batas_free_ditolak(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.status_langganan = StatusLangganan.PRO
    pengguna.masa_berlaku_pro = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    id_batch = await _buat_batch(client, token)
    db_session.add_all(
        [
            Soal(id_batch=uuid.UUID(id_batch), no_soal=nomor, kunci_jawaban=f"Kunci {nomor}")
            for nomor in range(1, 17)
        ]
    )
    await db_session.commit()
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 15 soal per batch.",
    }


async def test_ocr_kunci_batch_milik_pengajar_lain(client: AsyncClient, monkeypatch) -> None:
    token_a = await _token(client, "a@contoh.com")
    id_batch = await _buat_batch(client, token_a)
    token_b = await _token(client, "b@contoh.com")
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{id_batch}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token_b),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_ocr_kunci_batch_tidak_ada(client: AsyncClient, monkeypatch) -> None:
    token = await _token(client)
    _mock_ocr_kunci(monkeypatch, teks="tidak akan tercapai")

    response = await client.post(
        f"/api/batch/{uuid.uuid4()}/soal/ocr-kunci",
        files={"file": ("kunci.png", _PNG, "image/png")},
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"
