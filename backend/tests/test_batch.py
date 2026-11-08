import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.batch import Batch
from app.models.enums import Kategori, StatusBatch, StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import gemini, pemrosesan

_DAFTAR = {"nama": "Budi Santoso", "email": "Budi@Contoh.com", "password": "rahasia123"}
_PNG = b"\x89PNG\r\n\x1a\n" + b"konten png palsu"


@pytest.fixture(autouse=True)
def _upload_dir_sementara(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


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


async def _unggah_satu_jawaban(client: AsyncClient, token: str, id_batch: str) -> dict:
    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=[("files", ("a.png", _PNG, "image/png"))],
        data={"nama_peserta_didik": ["Budi"]},
        headers=_auth(token),
    )
    assert response.status_code == 201
    return response.json()[0]


async def _tandai_gagal(
    db_session: AsyncSession, id_file: str, pesan_error: str = "Pesan kesalahan lama"
) -> None:
    fj = await db_session.get(FileJawaban, uuid.UUID(id_file))
    fj.status_proses = StatusProses.GAGAL
    fj.pesan_error = pesan_error
    await db_session.commit()


async def _ambil_id_soal(db_session: AsyncSession, id_batch: str) -> str:
    id_soal = await db_session.scalar(
        select(Soal.id_soal).where(Soal.id_batch == uuid.UUID(id_batch))
    )
    return str(id_soal)


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

    pertama = await client.post("/api/batch", json={"nama_batch": "Pertama"}, headers=_auth(token))
    id_pertama = pertama.json()["id_batch"]
    await client.post(f"/api/batch/{id_pertama}/selesaikan", headers=_auth(token))
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


async def test_tambah_soal_ke_16_ditolak(client: AsyncClient) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    for nomor in range(1, 16):
        response = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert response.status_code == 201

    response = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci ke-16"},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 15 soal per batch.",
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


async def test_hapus_batch_sukses_beserta_berkas(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    rel_path = (
        await db_session.scalar(
            select(FileJawaban).where(FileJawaban.id_file == uuid.UUID(fj["id_file"]))
        )
    ).path
    assert (tmp_path / rel_path).exists()

    response = await client.delete(f"/api/batch/{id_batch}", headers=_auth(token))
    assert response.status_code == 204

    response = await client.get(f"/api/batch/{id_batch}", headers=_auth(token))
    assert response.status_code == 404

    assert await db_session.get(Batch, uuid.UUID(id_batch)) is None
    assert not (tmp_path / "uploads" / id_batch).exists()


async def test_hapus_batch_404_milik_pengguna_lain(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")

    buat = await client.post("/api/batch", json={"nama_batch": "Batch A"}, headers=_auth(token_a))
    id_batch = buat.json()["id_batch"]

    response = await client.delete(f"/api/batch/{id_batch}", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_hapus_batch_404_id_acak(client: AsyncClient) -> None:
    token = await _token(client)

    response = await client.delete(f"/api/batch/{uuid.uuid4()}", headers=_auth(token))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_hapus_batch_berstatus_selesai_boleh(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    batch = await db_session.get(Batch, uuid.UUID(id_batch))
    batch.status = StatusBatch.SELESAI
    await db_session.commit()

    response = await client.delete(f"/api/batch/{id_batch}", headers=_auth(token))
    assert response.status_code == 204


async def test_hapus_batch_saat_ada_file_diproses_boleh(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    """FR22 tidak mensyaratkan menunggu pemrosesan selesai (berbeda dari FR23).
    Keamanan tugas latar terhadap race ini dibuktikan terpisah di
    test_pemrosesan.py (batch dihapus lewat sesi lain saat tugas latar
    berjalan)."""
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    assert fj["status_proses"] == "diproses"

    response = await client.delete(f"/api/batch/{id_batch}", headers=_auth(token))
    assert response.status_code == 204
    assert await db_session.get(Batch, uuid.UUID(id_batch)) is None


async def test_hapus_batch_tanpa_token(client: AsyncClient) -> None:
    response = await client.delete(f"/api/batch/{uuid.uuid4()}")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_selesaikan_batch_sukses(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    response = await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["status"] == "selesai"

    response = await client.get(f"/api/batch/{id_batch}", headers=_auth(token))
    assert response.json()["status"] == "selesai"


async def test_selesaikan_batch_dengan_file_diproses_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await _unggah_satu_jawaban(client, token, id_batch)

    response = await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))
    assert response.status_code == 400
    assert response.json() == {
        "kode": "MASIH_ADA_FILE_DIPROSES",
        "pesan": "Tunggu hingga semua file selesai diproses.",
    }

    batch = await db_session.get(Batch, uuid.UUID(id_batch))
    assert batch.status == StatusBatch.AKTIF


async def test_selesaikan_batch_dua_kali_ditolak(client: AsyncClient) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)

    pertama = await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))
    assert pertama.status_code == 200

    kedua = await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))
    assert kedua.status_code == 400
    assert kedua.json() == {
        "kode": "BATCH_SUDAH_SELESAI",
        "pesan": "Batch yang sudah selesai tidak dapat diubah lagi.",
    }


async def test_selesaikan_batch_404_milik_pengguna_lain(client: AsyncClient) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")

    buat = await client.post("/api/batch", json={"nama_batch": "Batch A"}, headers=_auth(token_a))
    id_batch = buat.json()["id_batch"]

    response = await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token_b))
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_selesaikan_batch_tanpa_token(client: AsyncClient) -> None:
    response = await client.post(f"/api/batch/{uuid.uuid4()}/selesaikan")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_tambah_soal_ke_batch_selesai_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))

    jumlah_sebelum = len(
        list(await db_session.scalars(select(Soal).where(Soal.id_batch == uuid.UUID(id_batch))))
    )

    response = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci baru"},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATCH_SUDAH_SELESAI",
        "pesan": "Batch yang sudah selesai tidak dapat diubah lagi.",
    }

    jumlah_sesudah = len(
        list(await db_session.scalars(select(Soal).where(Soal.id_batch == uuid.UUID(id_batch))))
    )
    assert jumlah_sesudah == jumlah_sebelum


async def test_unggah_jawaban_ke_batch_selesai_ditolak(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    await client.post(f"/api/batch/{id_batch}/selesaikan", headers=_auth(token))

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban",
        files=[("files", ("a.png", _PNG, "image/png"))],
        data={"nama_peserta_didik": ["Budi"]},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATCH_SUDAH_SELESAI",
        "pesan": "Batch yang sudah selesai tidak dapat diubah lagi.",
    }

    jumlah_file = await db_session.scalar(
        select(FileJawaban).where(FileJawaban.id_batch == uuid.UUID(id_batch))
    )
    assert jumlah_file is None
    assert not any(p.is_file() for p in tmp_path.rglob("*"))


async def test_coba_lagi_sukses_sampai_selesai(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path,
    monkeypatch,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status_proses"] == "diproses"
    assert body["pesan_error"] is None

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=90)])
        ),
    )
    func, args, kwargs = _background_tasks_tidak_dijalankan[-1]
    assert func is pemrosesan.proses_file_jawaban
    await func(*args, db=db_session, **kwargs)

    response = await client.get(f"/api/batch/{id_batch}/file-jawaban", headers=_auth(token))
    daftar = response.json()
    assert daftar[0]["status_proses"] == "selesai"


async def test_coba_lagi_jumlah_retry_bertambah(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    sebelum = await db_session.get(FileJawaban, uuid.UUID(fj["id_file"]))
    assert sebelum.jumlah_retry == 0

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 200

    sesudah = await db_session.get(FileJawaban, uuid.UUID(fj["id_file"]))
    await db_session.refresh(sesudah)
    assert sesudah.jumlah_retry == 1


async def test_coba_lagi_file_bukan_gagal_ditolak(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    assert fj["status_proses"] == "diproses"

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "FILE_BUKAN_GAGAL",
        "pesan": "File ini tidak berstatus Gagal.",
    }


async def test_coba_lagi_batch_sudah_selesai_ditolak(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    batch = await db_session.get(Batch, uuid.UUID(id_batch))
    batch.status = StatusBatch.SELESAI
    await db_session.commit()

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 400
    assert response.json() == {
        "kode": "BATCH_SUDAH_SELESAI",
        "pesan": "Batch yang sudah selesai tidak dapat diubah lagi.",
    }


async def test_coba_lagi_file_milik_batch_lain_404(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token = await _token(client)
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == "budi@contoh.com"))
    pengguna.status_langganan = StatusLangganan.PRO
    await db_session.commit()

    id_batch_a = await _buat_batch_dengan_soal(client, token)
    id_batch_b = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch_a)
    await _tandai_gagal(db_session, fj["id_file"])

    response = await client.post(
        f"/api/batch/{id_batch_b}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 404
    assert response.json() == {
        "kode": "FILE_JAWABAN_TIDAK_DITEMUKAN",
        "pesan": "File jawaban tidak ditemukan.",
    }


async def test_coba_lagi_klik_ganda_tidak_memicu_dua_pemrosesan(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])
    jumlah_sebelum_retry = len(_background_tasks_tidak_dijalankan)

    pertama = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert pertama.status_code == 200

    kedua = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert kedua.status_code == 400
    assert kedua.json()["kode"] == "FILE_BUKAN_GAGAL"

    assert len(_background_tasks_tidak_dijalankan) == jumlah_sebelum_retry + 1


async def test_coba_lagi_gagal_lagi_pesan_error_baru(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path,
    monkeypatch,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 200

    monkeypatch.setattr(gemini, "ocr_grup", AsyncMock(side_effect=gemini.GagalPermanen()))
    func, args, kwargs = _background_tasks_tidak_dijalankan[-1]
    await func(*args, db=db_session, **kwargs)

    sesudah = await db_session.get(FileJawaban, uuid.UUID(fj["id_file"]))
    await db_session.refresh(sesudah)
    assert sesudah.status_proses == StatusProses.GAGAL
    assert sesudah.pesan_error == "Gagal membaca file, silakan coba lagi."
    assert sesudah.jumlah_retry == 1


async def test_coba_lagi_upsert_tidak_menyentuh_skor_revisi(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path,
    monkeypatch,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    id_soal = await _ambil_id_soal(db_session, id_batch)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    db_session.add(
        HasilKoreksi(
            id_file=uuid.UUID(fj["id_file"]),
            id_soal=uuid.UUID(id_soal),
            teks_ocr="Jawaban lama",
            skor_sistem=50,
            kategori=Kategori.KURANG_MIRIP,
            skor_revisi=77,
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 200

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban baru")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=95)])
        ),
    )
    func, args, kwargs = _background_tasks_tidak_dijalankan[-1]
    await func(*args, db=db_session, **kwargs)

    hasil = await db_session.scalar(
        select(HasilKoreksi).where(HasilKoreksi.id_file == uuid.UUID(fj["id_file"]))
    )
    await db_session.refresh(hasil)
    assert hasil.skor_sistem == 95
    assert hasil.teks_ocr == "Jawaban baru"
    assert hasil.skor_revisi == 77


async def test_coba_lagi_ocr_sukses_judge_gagal_lalu_retry_sukses(
    client: AsyncClient,
    db_session: AsyncSession,
    tmp_path,
    monkeypatch,
    _background_tasks_tidak_dijalankan: list[tuple],
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch_dengan_soal(client, token)
    id_soal = await _ambil_id_soal(db_session, id_batch)
    fj = await _unggah_satu_jawaban(client, token, id_batch)
    await _tandai_gagal(
        db_session,
        fj["id_file"],
        pesan_error="Layanan AI sedang sibuk atau kuota harian habis, coba lagi nanti.",
    )
    db_session.add(
        HasilKoreksi(
            id_file=uuid.UUID(fj["id_file"]),
            id_soal=uuid.UUID(id_soal),
            teks_ocr="Jawaban",
            skor_sistem=None,
            kategori=None,
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token)
    )
    assert response.status_code == 200

    monkeypatch.setattr(
        gemini,
        "ocr_grup",
        AsyncMock(
            return_value=gemini.ResponsOcr(
                items=[gemini.HasilOcrItem(id_item="0:1", teks="Jawaban")]
            )
        ),
    )
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item="0:1", skor=80)])
        ),
    )
    func, args, kwargs = _background_tasks_tidak_dijalankan[-1]
    await func(*args, db=db_session, **kwargs)

    fj_sesudah = await db_session.get(FileJawaban, uuid.UUID(fj["id_file"]))
    await db_session.refresh(fj_sesudah)
    assert fj_sesudah.status_proses == StatusProses.SELESAI

    hasil = await db_session.scalar(
        select(HasilKoreksi).where(HasilKoreksi.id_file == uuid.UUID(fj["id_file"]))
    )
    await db_session.refresh(hasil)
    assert hasil.skor_sistem == 80


async def test_coba_lagi_404_batch_milik_pengguna_lain(
    client: AsyncClient, db_session: AsyncSession, tmp_path
) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")
    id_batch = await _buat_batch_dengan_soal(client, token_a)
    fj = await _unggah_satu_jawaban(client, token_a, id_batch)
    await _tandai_gagal(db_session, fj["id_file"])

    response = await client.post(
        f"/api/batch/{id_batch}/file-jawaban/{fj['id_file']}/coba-lagi", headers=_auth(token_b)
    )
    assert response.status_code == 404
    assert response.json() == {
        "kode": "BATCH_TIDAK_DITEMUKAN",
        "pesan": "Batch tidak ditemukan",
    }


async def test_coba_lagi_tanpa_token(client: AsyncClient) -> None:
    response = await client.post(f"/api/batch/{uuid.uuid4()}/file-jawaban/{uuid.uuid4()}/coba-lagi")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


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


async def test_buat_batch_kedua_akun_free_saat_batch_pertama_aktif_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)

    pertama = await client.post(
        "/api/batch", json={"nama_batch": "Batch Pertama"}, headers=_auth(token)
    )
    assert pertama.status_code == 201

    kedua = await client.post(
        "/api/batch", json={"nama_batch": "Batch Kedua"}, headers=_auth(token)
    )
    assert kedua.status_code == 400
    assert kedua.json() == {
        "kode": "BATAS_BATCH_AKTIF_TERCAPAI",
        "pesan": (
            "Batas batch aktif untuk akun Free telah tercapai. "
            "Upgrade ke Pro untuk batch tidak terbatas."
        ),
    }

    jumlah_batch = await db_session.scalar(select(func.count()).select_from(Batch))
    assert jumlah_batch == 1


async def test_buat_batch_kedua_akun_free_setelah_batch_pertama_selesai_boleh(
    client: AsyncClient,
) -> None:
    token = await _token(client)

    pertama = await client.post(
        "/api/batch", json={"nama_batch": "Batch Pertama"}, headers=_auth(token)
    )
    id_pertama = pertama.json()["id_batch"]

    selesai = await client.post(f"/api/batch/{id_pertama}/selesaikan", headers=_auth(token))
    assert selesai.status_code == 200

    kedua = await client.post(
        "/api/batch", json={"nama_batch": "Batch Kedua"}, headers=_auth(token)
    )
    assert kedua.status_code == 201
    assert kedua.json()["nama_batch"] == "Batch Kedua"
    assert kedua.json()["status"] == "aktif"


async def test_buat_batch_kedua_akun_free_setelah_batch_pertama_dihapus_boleh(
    client: AsyncClient,
) -> None:
    token = await _token(client)

    pertama = await client.post(
        "/api/batch", json={"nama_batch": "Batch Pertama"}, headers=_auth(token)
    )
    id_pertama = pertama.json()["id_batch"]

    hapus = await client.delete(f"/api/batch/{id_pertama}", headers=_auth(token))
    assert hapus.status_code == 204

    kedua = await client.post(
        "/api/batch", json={"nama_batch": "Batch Kedua"}, headers=_auth(token)
    )
    assert kedua.status_code == 201


async def test_buat_banyak_batch_aktif_akun_pro_boleh(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) + timedelta(days=30),
    )

    for nomor in (1, 2, 3):
        res = await client.post(
            "/api/batch", json={"nama_batch": f"Batch Pro {nomor}"}, headers=_auth(token)
        )
        assert res.status_code == 201

    daftar = await client.get("/api/batch", headers=_auth(token))
    assert len(daftar.json()) == 3


async def test_buat_batch_akun_pro_kedaluwarsa_diperlakukan_sebagai_free(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) + timedelta(days=30),
    )

    b1 = await client.post("/api/batch", json={"nama_batch": "Batch 1"}, headers=_auth(token))
    b2 = await client.post("/api/batch", json={"nama_batch": "Batch 2"}, headers=_auth(token))
    assert b1.status_code == 201
    assert b2.status_code == 201
    id_b1 = b1.json()["id_batch"]
    id_b2 = b2.json()["id_batch"]

    # Masa berlaku Pro lewat: akun efektif kembali ke Free.
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) - timedelta(seconds=1),
    )

    # Data lama tidak dihapus dan tetap dapat dibuka.
    daftar = await client.get("/api/batch", headers=_auth(token))
    assert len(daftar.json()) == 2
    assert (await client.get(f"/api/batch/{id_b1}", headers=_auth(token))).status_code == 200
    assert (await client.get(f"/api/batch/{id_b2}", headers=_auth(token))).status_code == 200

    # Buat batch ke-3 ditolak karena masih punya >0 batch aktif.
    b3 = await client.post("/api/batch", json={"nama_batch": "Batch 3"}, headers=_auth(token))
    assert b3.status_code == 400
    assert b3.json()["kode"] == "BATAS_BATCH_AKTIF_TERCAPAI"

    # Selesaikan satu batch: sisa 1 batch aktif, buat batch baru masih ditolak.
    await client.post(f"/api/batch/{id_b1}/selesaikan", headers=_auth(token))
    b3_masih_ditolak = await client.post(
        "/api/batch", json={"nama_batch": "Batch 3"}, headers=_auth(token)
    )
    assert b3_masih_ditolak.status_code == 400
    assert b3_masih_ditolak.json()["kode"] == "BATAS_BATCH_AKTIF_TERCAPAI"

    # Selesaikan batch aktif kedua: sisa 0 batch aktif, kini bisa membuat batch baru.
    await client.post(f"/api/batch/{id_b2}/selesaikan", headers=_auth(token))
    b3_sukses = await client.post(
        "/api/batch", json={"nama_batch": "Batch 3"}, headers=_auth(token)
    )
    assert b3_sukses.status_code == 201


async def test_tambah_soal_akun_pro_sampai_30_sukses_dan_ke_31_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) + timedelta(days=30),
    )

    buat = await client.post("/api/batch", json={"nama_batch": "Batch Pro"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    for nomor in range(1, 31):
        response = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert response.status_code == 201
        assert response.json()["no_soal"] == nomor

    ke_31 = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci ke-31"},
        headers=_auth(token),
    )
    assert ke_31.status_code == 400
    assert ke_31.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 30 soal per batch.",
    }


async def test_tambah_soal_akun_pro_kedaluwarsa_di_atas_batas_free_ditolak_data_lama_utuh(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) + timedelta(days=30),
    )

    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    for nomor in range(1, 21):
        res = await client.post(
            f"/api/batch/{id_batch}/soal",
            json={"kunci_jawaban": f"Kunci {nomor}"},
            headers=_auth(token),
        )
        assert res.status_code == 201

    # Masa berlaku Pro lewat saat batch sudah berisi 20 soal (>15).
    await _set_langganan(
        db_session,
        "budi@contoh.com",
        StatusLangganan.PRO,
        datetime.now(UTC) - timedelta(seconds=1),
    )

    daftar = await client.get(f"/api/batch/{id_batch}/soal", headers=_auth(token))
    assert daftar.status_code == 200
    assert len(daftar.json()) == 20

    ke_21 = await client.post(
        f"/api/batch/{id_batch}/soal",
        json={"kunci_jawaban": "Kunci ke-21"},
        headers=_auth(token),
    )
    assert ke_21.status_code == 400
    assert ke_21.json() == {
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 15 soal per batch.",
    }


async def test_balapan_buat_batch_akun_free_hanya_satu_lolos(
    client: AsyncClient, db_session: AsyncSession, _engine
) -> None:
    token = await _token(client)

    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async def _get_db_per_request() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as sesi:
            yield sesi

    override_lama = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db_per_request
    try:
        r1, r2 = await asyncio.gather(
            client.post("/api/batch", json={"nama_batch": "Balapan 1"}, headers=_auth(token)),
            client.post("/api/batch", json={"nama_batch": "Balapan 2"}, headers=_auth(token)),
        )
    finally:
        if override_lama is not None:
            app.dependency_overrides[get_db] = override_lama
        else:
            app.dependency_overrides.pop(get_db, None)

    assert sorted([r1.status_code, r2.status_code]) == [201, 400]
    gagal = r1 if r1.status_code == 400 else r2
    assert gagal.json()["kode"] == "BATAS_BATCH_AKTIF_TERCAPAI"

    jumlah_aktif = await db_session.scalar(
        select(func.count()).select_from(Batch).where(Batch.status != StatusBatch.SELESAI)
    )
    assert jumlah_aktif == 1


async def test_balapan_tambah_soal_pada_batas_hanya_satu_lolos(
    client: AsyncClient, db_session: AsyncSession, _engine
) -> None:
    token = await _token(client)
    buat = await client.post("/api/batch", json={"nama_batch": "Batch"}, headers=_auth(token))
    id_batch = buat.json()["id_batch"]

    db_session.add_all(
        [
            Soal(id_batch=uuid.UUID(id_batch), no_soal=nomor, kunci_jawaban=f"Kunci {nomor}")
            for nomor in range(1, 15)
        ]
    )
    await db_session.commit()

    sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async def _get_db_per_request() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as sesi:
            yield sesi

    override_lama = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db_per_request
    try:
        r1, r2 = await asyncio.gather(
            client.post(
                f"/api/batch/{id_batch}/soal",
                json={"kunci_jawaban": "Kunci balapan A"},
                headers=_auth(token),
            ),
            client.post(
                f"/api/batch/{id_batch}/soal",
                json={"kunci_jawaban": "Kunci balapan B"},
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
        "kode": "BATAS_SOAL_TERLAMPAUI",
        "pesan": "Sudah mencapai jumlah maksimal 15 soal per batch.",
    }

    jumlah_soal = await db_session.scalar(
        select(func.count()).select_from(Soal).where(Soal.id_batch == uuid.UUID(id_batch))
    )
    assert jumlah_soal == 15
