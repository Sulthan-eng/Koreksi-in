import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch
from app.models.enums import Kategori, StatusBatch, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.services import gemini

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
    skor_hitung_ulang: bool = False,
) -> HasilKoreksi:
    baris = HasilKoreksi(
        id_file=id_file,
        id_soal=uuid.UUID(id_soal),
        teks_ocr=teks_ocr,
        skor_sistem=skor_sistem,
        kategori=kategori,
        skor_hitung_ulang=skor_hitung_ulang,
    )
    db_session.add(baris)
    await db_session.commit()
    return baris


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


async def _siapkan_hasil(
    client: AsyncClient,
    db_session: AsyncSession,
    token: str,
    teks_ocr: str = "Jawaban lama",
    skor_sistem: int = 50,
    kategori: Kategori = Kategori.CUKUP_MIRIP,
    skor_hitung_ulang: bool = False,
) -> tuple[str, HasilKoreksi]:
    id_batch = await _buat_batch(client, token)
    id_soal = await _tambah_soal(client, token, id_batch, "Kunci Jawaban Benar")
    file_selesai = await _buat_file_jawaban(db_session, id_batch, "Budi", StatusProses.SELESAI)
    baris = await _buat_hasil_koreksi(
        db_session,
        file_selesai.id_file,
        id_soal,
        teks_ocr=teks_ocr,
        skor_sistem=skor_sistem,
        kategori=kategori,
        skor_hitung_ulang=skor_hitung_ulang,
    )
    return id_batch, baris


async def test_edit_teks_ocr_sukses_skor_berubah(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    judge_mock = AsyncMock(
        return_value=gemini.ResponsJudge(
            items=[gemini.HasilJudgeItem(id_item=str(baris.id_koreksi), skor=95)]
        )
    )
    monkeypatch.setattr(gemini, "judge_grup", judge_mock)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru yang benar"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["teks_ocr"] == "Jawaban baru yang benar"
    assert body["skor_sistem"] == 95
    assert body["kategori"] == "sangat_mirip"
    assert body["skor_hitung_ulang"] is False
    judge_mock.assert_awaited_once()


async def test_edit_teks_ocr_tidak_berubah_tanpa_panggilan_judge(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token, teks_ocr="Jawaban lama")
    judge_mock = AsyncMock()
    monkeypatch.setattr(gemini, "judge_grup", judge_mock)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban lama"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["teks_ocr"] == "Jawaban lama"
    assert body["skor_sistem"] == 50
    judge_mock.assert_not_awaited()


async def test_edit_teks_ocr_hanya_beda_whitespace_tanpa_panggilan_judge(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    """teks_ocr tersimpan berakhiran spasi/newline (umum dari hasil OCR); teks yang
    dikirim sama setelah di-trim harus dianggap tidak berubah (NFR14), tanpa
    memanggil judge dan tanpa menulis ulang teks tersimpan."""
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token, teks_ocr="Jawaban lama  \n")
    judge_mock = AsyncMock()
    monkeypatch.setattr(gemini, "judge_grup", judge_mock)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban lama"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["teks_ocr"] == "Jawaban lama  \n"
    assert body["skor_sistem"] == 50
    judge_mock.assert_not_awaited()


async def test_edit_teks_ocr_kosong_ditolak(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "   "},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "TEKS_OCR_KOSONG"


async def test_edit_teks_ocr_terlalu_panjang_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "a" * 10_001},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "TEKS_OCR_TERLALU_PANJANG"


async def test_edit_teks_ocr_judge_gagal_menyimpan_teks_dan_menyalakan_hitung_ulang(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(
        client, db_session, token, skor_sistem=50, kategori=Kategori.CUKUP_MIRIP
    )
    monkeypatch.setattr(gemini, "judge_grup", AsyncMock(side_effect=gemini.GagalPermanen()))

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["teks_ocr"] == "Jawaban baru"
    assert body["skor_sistem"] == 50
    assert body["kategori"] == "cukup_mirip"
    assert body["skor_hitung_ulang"] is True


async def test_edit_teks_ocr_kuota_habis(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(
        client, db_session, token, skor_sistem=50, kategori=Kategori.CUKUP_MIRIP
    )
    monkeypatch.setattr(gemini, "judge_grup", AsyncMock(side_effect=gemini.KuotaHarianHabis()))

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["teks_ocr"] == "Jawaban baru"
    assert body["skor_sistem"] == 50
    assert body["skor_hitung_ulang"] is True


async def test_edit_teks_ocr_exception_tak_dikenal_teks_dan_flag_tetap_tersimpan(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    """Exception tak dikenal dari judge TIDAK ditangkap, jadi menjalar (di produksi
    ini menjadi 500 lewat ServerErrorMiddleware uvicorn; lewat ASGITransport di
    test, exception Python menjalar langsung ke pemanggil)."""
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    monkeypatch.setattr(gemini, "judge_grup", AsyncMock(side_effect=RuntimeError("tak terduga")))

    with pytest.raises(RuntimeError, match="tak terduga"):
        await client.patch(
            f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
            json={"teks_ocr": "Jawaban baru"},
            headers=_auth(token),
        )

    baris_db = await db_session.get(HasilKoreksi, baris.id_koreksi)
    assert baris_db.teks_ocr == "Jawaban baru"
    assert baris_db.skor_hitung_ulang is True


async def test_edit_teks_ocr_batch_selesai_ditolak(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    batch = await db_session.get(Batch, uuid.UUID(id_batch))
    batch.status = StatusBatch.SELESAI
    await db_session.commit()

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 400
    assert response.json()["kode"] == "BATCH_SUDAH_SELESAI"


async def test_edit_teks_ocr_milik_pengajar_lain_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token_a = await _token(client, "a2@contoh.com")
    token_b = await _token(client, "b2@contoh.com")
    id_batch, baris = await _siapkan_hasil(client, db_session, token_a)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token_b),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_edit_teks_ocr_id_koreksi_acak_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch, _ = await _siapkan_hasil(client, db_session, token)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{uuid.uuid4()}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "HASIL_KOREKSI_TIDAK_DITEMUKAN"


async def test_edit_teks_ocr_file_belum_selesai_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token(client)
    id_batch = await _buat_batch(client, token)
    id_soal = await _tambah_soal(client, token, id_batch)
    file_diproses = await _buat_file_jawaban(db_session, id_batch, "Ani", StatusProses.DIPROSES)
    baris = await _buat_hasil_koreksi(db_session, file_diproses.id_file, id_soal)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "HASIL_KOREKSI_TIDAK_DITEMUKAN"


async def test_edit_teks_ocr_skor_revisi_tidak_berubah(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    baris.skor_revisi = 77
    await db_session.commit()
    monkeypatch.setattr(
        gemini,
        "judge_grup",
        AsyncMock(
            return_value=gemini.ResponsJudge(
                items=[gemini.HasilJudgeItem(id_item=str(baris.id_koreksi), skor=95)]
            )
        ),
    )

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban baru yang benar"},
        headers=_auth(token),
    )
    assert response.status_code == 200

    baris_db = await db_session.get(HasilKoreksi, baris.id_koreksi, populate_existing=True)
    assert baris_db.skor_revisi == 77


async def test_edit_teks_ocr_sama_tapi_hitung_ulang_true_panggil_judge_lagi(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(
        client,
        db_session,
        token,
        teks_ocr="Jawaban lama",
        skor_sistem=50,
        kategori=Kategori.CUKUP_MIRIP,
        skor_hitung_ulang=True,
    )
    judge_mock = AsyncMock(
        return_value=gemini.ResponsJudge(
            items=[gemini.HasilJudgeItem(id_item=str(baris.id_koreksi), skor=10)]
        )
    )
    monkeypatch.setattr(gemini, "judge_grup", judge_mock)

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{baris.id_koreksi}",
        json={"teks_ocr": "Jawaban lama"},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["skor_sistem"] == 10
    assert body["kategori"] == "kurang_mirip"
    assert body["skor_hitung_ulang"] is False
    judge_mock.assert_awaited_once()


async def test_edit_teks_ocr_dua_edit_overtaking_tidak_menimpa_skor_usang(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, _engine
) -> None:
    """Edit pertama mengubah teks ke A, lalu sebelum judge-nya 'selesai', edit lain
    (disimulasikan langsung lewat sesi DB terpisah) sudah menimpa teks ke B. UPDATE
    skor dari penilaian teks A tidak boleh tertulis karena teks_ocr di DB sudah
    bukan A."""
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    id_koreksi = baris.id_koreksi

    async def _judge_dengan_overtake(items):
        from sqlalchemy.ext.asyncio import async_sessionmaker

        sesi_lain = async_sessionmaker(_engine, expire_on_commit=False)
        async with sesi_lain() as sesi:
            await sesi.execute(
                HasilKoreksi.__table__.update()
                .where(HasilKoreksi.id_koreksi == id_koreksi)
                .values(teks_ocr="Teks B dari edit lain", skor_hitung_ulang=True)
            )
            await sesi.commit()
        return gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item=str(id_koreksi), skor=99)])

    monkeypatch.setattr(gemini, "judge_grup", AsyncMock(side_effect=_judge_dengan_overtake))

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{id_koreksi}",
        json={"teks_ocr": "Teks A"},
        headers=_auth(token),
    )
    assert response.status_code == 200

    baris_db = await db_session.get(HasilKoreksi, id_koreksi, populate_existing=True)
    assert baris_db.teks_ocr == "Teks B dari edit lain"
    assert baris_db.skor_sistem != 99


async def test_edit_teks_ocr_batch_terhapus_saat_judge_berjalan(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, _engine
) -> None:
    """Batch (dan turunannya lewat cascade) terhapus oleh request lain selagi
    judge masih berjalan. Re-select baris setelah judge mengembalikan None;
    endpoint harus melempar HASIL_KOREKSI_TIDAK_DITEMUKAN, bukan error tak
    terduga."""
    token = await _token(client)
    id_batch, baris = await _siapkan_hasil(client, db_session, token)
    id_koreksi = baris.id_koreksi

    async def _judge_dengan_hapus_batch(items):
        from sqlalchemy.ext.asyncio import async_sessionmaker

        sesi_lain = async_sessionmaker(_engine, expire_on_commit=False)
        async with sesi_lain() as sesi:
            batch_lain = await sesi.get(Batch, uuid.UUID(id_batch))
            await sesi.delete(batch_lain)
            await sesi.commit()
        return gemini.ResponsJudge(items=[gemini.HasilJudgeItem(id_item=str(id_koreksi), skor=90)])

    monkeypatch.setattr(gemini, "judge_grup", AsyncMock(side_effect=_judge_dengan_hapus_batch))

    response = await client.patch(
        f"/api/batch/{id_batch}/hasil/{id_koreksi}",
        json={"teks_ocr": "Jawaban baru"},
        headers=_auth(token),
    )
    assert response.status_code == 404
    assert response.json()["kode"] == "HASIL_KOREKSI_TIDAK_DITEMUKAN"
