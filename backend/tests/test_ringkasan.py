import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.enums import StatusBatch, StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.pengguna import Pengguna
from app.services.langganan import BATAS_PER_JENIS_AKUN

_FREE = BATAS_PER_JENIS_AKUN[StatusLangganan.FREE]
_PRO = BATAS_PER_JENIS_AKUN[StatusLangganan.PRO]

_DAFTAR = {"nama": "Budi Santoso", "email": "budi@contoh.com", "password": "rahasia123"}


async def _daftar_dan_masuk(client: AsyncClient, email: str = "budi@contoh.com") -> dict:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    hasil = await _daftar_dan_masuk(client, email)
    return hasil["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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


async def _buat_batch(
    db_session: AsyncSession,
    email: str,
    status: StatusBatch = StatusBatch.AKTIF,
    nama_batch: str = "Batch",
    dibuat_pada: datetime | None = None,
) -> uuid.UUID:
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == email))
    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch=nama_batch, status=status)
    if dibuat_pada is not None:
        batch.dibuat_pada = dibuat_pada
    db_session.add(batch)
    await db_session.commit()
    return batch.id_batch


async def _isi_file_jawaban(
    db_session: AsyncSession, id_batch: uuid.UUID, status_list: list[StatusProses]
) -> None:
    db_session.add_all(
        [
            FileJawaban(
                id_batch=id_batch,
                nama_peserta_didik=f"Peserta {i + 1}",
                path=f"uploads/{id_batch}/{i + 1}.png",
                status_proses=status,
            )
            for i, status in enumerate(status_list)
        ]
    )
    await db_session.commit()


async def test_ringkasan_free_tanpa_batch(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _token(client)

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "total_batch": 0,
        "peserta_didik_dikoreksi": 0,
        "sisa_slot_batch_aktif": _FREE.maks_batch_aktif,
        "sisa_slot_jawaban_per_batch": _FREE.maks_jawaban_per_batch,
    }


async def test_ringkasan_free_batch_aktif_dengan_status_campuran(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(db_session, "budi@contoh.com")
    await _isi_file_jawaban(
        db_session,
        id_batch,
        [StatusProses.DIPROSES, StatusProses.SELESAI, StatusProses.SELESAI, StatusProses.GAGAL],
    )

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "total_batch": 1,
        "peserta_didik_dikoreksi": 2,
        "sisa_slot_batch_aktif": _FREE.maks_batch_aktif - 1,
        "sisa_slot_jawaban_per_batch": _FREE.maks_jawaban_per_batch - 4,
    }


async def test_ringkasan_batch_selesai_tetap_terhitung(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(db_session, "budi@contoh.com", status=StatusBatch.SELESAI)
    await _isi_file_jawaban(
        db_session, id_batch, [StatusProses.SELESAI, StatusProses.SELESAI, StatusProses.GAGAL]
    )

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total_batch"] == 1
    assert body["peserta_didik_dikoreksi"] == 2
    # Tidak ada batch Aktif: sisa slot jawaban penuh, bukan dari batch Selesai ini.
    assert body["sisa_slot_batch_aktif"] == _FREE.maks_batch_aktif
    assert body["sisa_slot_jawaban_per_batch"] == _FREE.maks_jawaban_per_batch


async def test_ringkasan_pro_slot_null(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session, "budi@contoh.com", StatusLangganan.PRO, datetime.now(UTC) + timedelta(days=30)
    )
    id_batch = await _buat_batch(db_session, "budi@contoh.com")
    await _isi_file_jawaban(db_session, id_batch, [StatusProses.SELESAI])

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {
        "total_batch": 1,
        "peserta_didik_dikoreksi": 1,
        "sisa_slot_batch_aktif": None,
        "sisa_slot_jawaban_per_batch": None,
    }


async def test_ringkasan_pro_kedaluwarsa_diperlakukan_free(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session, "budi@contoh.com", StatusLangganan.PRO, datetime.now(UTC) - timedelta(seconds=1)
    )
    await _buat_batch(db_session, "budi@contoh.com")

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["sisa_slot_batch_aktif"] == _FREE.maks_batch_aktif - 1
    assert body["sisa_slot_jawaban_per_batch"] == _FREE.maks_jawaban_per_batch


async def test_ringkasan_beberapa_batch_aktif_pakai_terbaru_dan_jepit_nol(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session, "budi@contoh.com", StatusLangganan.PRO, datetime.now(UTC) + timedelta(days=30)
    )
    waktu_lama = datetime.now(UTC) - timedelta(hours=2)
    waktu_baru = datetime.now(UTC) - timedelta(hours=1)
    id_batch_lama = await _buat_batch(
        db_session, "budi@contoh.com", nama_batch="Lama", dibuat_pada=waktu_lama
    )
    id_batch_baru = await _buat_batch(
        db_session, "budi@contoh.com", nama_batch="Baru", dibuat_pada=waktu_baru
    )
    await _isi_file_jawaban(db_session, id_batch_lama, [StatusProses.SELESAI])
    await _isi_file_jawaban(
        db_session, id_batch_baru, [StatusProses.SELESAI, StatusProses.DIPROSES]
    )

    # Akun turun ke Free dengan 2 batch Aktif sekaligus.
    await _set_langganan(db_session, "budi@contoh.com", StatusLangganan.FREE)

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body["total_batch"] == 2
    assert body["peserta_didik_dikoreksi"] == 2
    # 2 batch Aktif > batas 1: dijepit ke 0, bukan negatif.
    assert body["sisa_slot_batch_aktif"] == 0
    # Batch terbaru (id_batch_baru) punya 2 file.
    assert body["sisa_slot_jawaban_per_batch"] == _FREE.maks_jawaban_per_batch - 2
    assert id_batch_lama != id_batch_baru


async def test_ringkasan_free_jawaban_di_batch_aktif_melebihi_batas_jepit_nol(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    await _set_langganan(
        db_session, "budi@contoh.com", StatusLangganan.PRO, datetime.now(UTC) + timedelta(days=30)
    )
    id_batch = await _buat_batch(db_session, "budi@contoh.com")
    await _isi_file_jawaban(
        db_session, id_batch, [StatusProses.SELESAI] * (_FREE.maks_jawaban_per_batch + 5)
    )

    # Akun turun ke Free: batch Aktif ini sudah melebihi batas jawaban Free.
    await _set_langganan(db_session, "budi@contoh.com", StatusLangganan.FREE)

    response = await client.get("/api/ringkasan", headers=_auth(token))

    assert response.status_code == 200
    assert response.json()["sisa_slot_jawaban_per_batch"] == 0


async def test_ringkasan_tidak_termasuk_data_pengajar_lain(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token_a = await _token(client, "a@contoh.com")
    token_b = await _token(client, "b@contoh.com")
    id_batch_b = await _buat_batch(db_session, "b@contoh.com")
    await _isi_file_jawaban(db_session, id_batch_b, [StatusProses.SELESAI, StatusProses.SELESAI])

    response_a = await client.get("/api/ringkasan", headers=_auth(token_a))
    response_b = await client.get("/api/ringkasan", headers=_auth(token_b))

    assert response_a.json() == {
        "total_batch": 0,
        "peserta_didik_dikoreksi": 0,
        "sisa_slot_batch_aktif": _FREE.maks_batch_aktif,
        "sisa_slot_jawaban_per_batch": _FREE.maks_jawaban_per_batch,
    }
    assert response_b.json()["total_batch"] == 1
    assert response_b.json()["peserta_didik_dikoreksi"] == 2


async def test_ringkasan_tanpa_token_401(client: AsyncClient) -> None:
    response = await client.get("/api/ringkasan")

    assert response.status_code == 401
