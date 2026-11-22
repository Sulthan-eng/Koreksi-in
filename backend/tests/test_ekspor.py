import io
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.batch import Batch
from app.models.enums import Kategori, StatusBatch, StatusLangganan, StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services import ekspor as ekspor_service

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS = {"s": _NS_MAIN}
_DAFTAR = {"nama": "Budi Santoso", "email": "budi@contoh.com", "password": "rahasia123"}


def _baca_xlsx(konten: bytes) -> dict:
    """Inspeksi langsung struktur OOXML (.xlsx) memakai stdlib zipfile + ElementTree
    agar isi sel, merge header, tipe sel (t='s'), tag formula (<f>), dan quotePrefix
    terverifikasi langsung pada berkas biner yang dihasilkan."""
    with zipfile.ZipFile(io.BytesIO(konten)) as zf:
        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        sheet_names = [el.attrib["name"] for el in wb_root.findall(".//s:sheets/s:sheet", _NS)]

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sst_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sst_root.findall("s:si", _NS):
                shared_strings.append("".join(t.text or "" for t in si.findall(".//s:t", _NS)))

        styles_root = ET.fromstring(zf.read("xl/styles.xml"))
        cell_xfs: list[dict[str, str]] = []
        cell_xfs_el = styles_root.find("s:cellXfs", _NS)
        if cell_xfs_el is not None:
            for xf in cell_xfs_el.findall("s:xf", _NS):
                cell_xfs.append(dict(xf.attrib))

        sheet_root = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        merges = {mc.attrib["ref"] for mc in sheet_root.findall(".//s:mergeCells/s:mergeCell", _NS)}

        formula_cells: list[str] = []
        cells: dict[str, dict] = {}
        for c in sheet_root.findall(".//s:sheetData/s:row/s:c", _NS):
            ref = c.attrib["r"]
            cell_type = c.attrib.get("t")
            style_idx = int(c.attrib["s"]) if "s" in c.attrib else None
            quote_prefix = False
            if style_idx is not None and style_idx < len(cell_xfs):
                quote_prefix = cell_xfs[style_idx].get("quotePrefix") == "1"

            f_el = c.find("s:f", _NS)
            if f_el is not None:
                formula_cells.append(ref)

            v_el = c.find("s:v", _NS)
            value: object = None
            if cell_type == "s" and v_el is not None and v_el.text is not None:
                value = shared_strings[int(v_el.text)]
            elif cell_type == "inlineStr":
                value = "".join(t.text or "" for t in c.findall(".//s:t", _NS))
            elif v_el is not None and v_el.text is not None:
                raw = v_el.text
                value = float(raw) if ("." in raw or "e" in raw.lower()) else int(raw)

            cells[ref] = {
                "type": cell_type,
                "value": value,
                "style_idx": style_idx,
                "quote_prefix": quote_prefix,
            }

    return {
        "sheet_names": sheet_names,
        "merges": merges,
        "formula_cells": formula_cells,
        "cells": cells,
    }


def _nilai_sel(wb: dict, ref: str) -> object:
    sel = wb["cells"].get(ref)
    return sel["value"] if sel is not None else None


async def _token(client: AsyncClient, email: str = "budi@contoh.com") -> str:
    await client.post("/api/auth/daftar", json={**_DAFTAR, "email": email})
    response = await client.post("/api/auth/masuk", json={"email": email, "password": "rahasia123"})
    return response.json()["access_token"]


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


async def _token_pro(
    client: AsyncClient,
    db_session: AsyncSession,
    email: str = "pro@contoh.com",
    masa_berlaku_pro: datetime | None = ...,
) -> str:
    token = await _token(client, email)
    batas = datetime.now(UTC) + timedelta(days=30) if masa_berlaku_pro is ... else masa_berlaku_pro
    await _set_langganan(db_session, email, StatusLangganan.PRO, batas)
    return token


async def _buat_batch(
    db_session: AsyncSession,
    email: str,
    nama_batch: str = "UTS Biologi",
    status: StatusBatch = StatusBatch.AKTIF,
) -> uuid.UUID:
    pengguna = await db_session.scalar(select(Pengguna).where(Pengguna.email == email))
    batch = Batch(id_pengguna=pengguna.id_pengguna, nama_batch=nama_batch, status=status)
    db_session.add(batch)
    await db_session.commit()
    return batch.id_batch


async def _tambah_soal_db(
    db_session: AsyncSession, id_batch: uuid.UUID, no_soal: int, kunci: str = "Kunci"
) -> uuid.UUID:
    soal = Soal(id_batch=id_batch, no_soal=no_soal, kunci_jawaban=kunci)
    db_session.add(soal)
    await db_session.commit()
    return soal.id_soal


async def _buat_file(
    db_session: AsyncSession,
    id_batch: uuid.UUID,
    nama_peserta_didik: str,
    status_proses: StatusProses,
    diunggah_pada: datetime | None = None,
    id_file: uuid.UUID | None = None,
) -> FileJawaban:
    fj = FileJawaban(
        **({"id_file": id_file} if id_file is not None else {}),
        id_batch=id_batch,
        nama_peserta_didik=nama_peserta_didik,
        path=f"uploads/{id_batch}/berkas.png",
        status_proses=status_proses,
        **({"diunggah_pada": diunggah_pada} if diunggah_pada is not None else {}),
    )
    db_session.add(fj)
    await db_session.commit()
    return fj


async def _buat_hasil(
    db_session: AsyncSession,
    id_file: uuid.UUID,
    id_soal: uuid.UUID,
    skor_sistem: int | None = 85,
    kategori: Kategori | None = Kategori.SANGAT_MIRIP,
    skor_revisi: int | None = None,
) -> HasilKoreksi:
    hasil = HasilKoreksi(
        id_file=id_file,
        id_soal=id_soal,
        teks_ocr="Jawaban",
        skor_sistem=skor_sistem,
        kategori=kategori,
        skor_revisi=skor_revisi,
    )
    db_session.add(hasil)
    await db_session.commit()
    return hasil


async def test_ekspor_tanpa_token_401(client: AsyncClient) -> None:
    response = await client.get(f"/api/batch/{uuid.uuid4()}/ekspor")
    assert response.status_code == 401
    assert response.json()["kode"] == "SESI_BERAKHIR"


async def test_ekspor_akun_free_ditolak_403(client: AsyncClient, db_session: AsyncSession) -> None:
    token = await _token(client, "free@contoh.com")
    id_batch = await _buat_batch(db_session, "free@contoh.com")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 403
    assert response.json() == {
        "kode": "EKSPOR_KHUSUS_PRO",
        "pesan": "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini.",
    }


async def test_ekspor_pro_kedaluwarsa_ditolak_403(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(
        client,
        db_session,
        email="kedaluwarsa@contoh.com",
        masa_berlaku_pro=datetime.now(UTC) - timedelta(seconds=1),
    )
    id_batch = await _buat_batch(db_session, "kedaluwarsa@contoh.com")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 403
    assert response.json()["kode"] == "EKSPOR_KHUSUS_PRO"


async def test_ekspor_pro_tanpa_masa_berlaku_berhasil(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session, email="pro_none@contoh.com", masa_berlaku_pro=None)
    id_batch = await _buat_batch(db_session, "pro_none@contoh.com", nama_batch="Kuis 1")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(ekspor_service.MEDIA_TYPE_XLSX)


async def test_ekspor_isolasi_batch_pengajar_lain_404(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token_a = await _token_pro(client, db_session, email="a@contoh.com")
    await _token_pro(client, db_session, email="b@contoh.com")
    id_batch_b = await _buat_batch(db_session, "b@contoh.com", nama_batch="Milik B")
    id_soal_b = await _tambah_soal_db(db_session, id_batch_b, 1)
    fj = await _buat_file(db_session, id_batch_b, "Siswa B", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal_b)

    resp_lain = await client.get(f"/api/batch/{id_batch_b}/ekspor", headers=_auth(token_a))
    resp_tidak_ada = await client.get(f"/api/batch/{uuid.uuid4()}/ekspor", headers=_auth(token_a))

    assert resp_lain.status_code == 404
    assert resp_lain.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"
    assert resp_tidak_ada.status_code == 404
    assert resp_tidak_ada.json()["kode"] == "BATCH_TIDAK_DITEMUKAN"


async def test_ekspor_batch_selesai_tetap_bisa_diekspor(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(
        db_session, "pro@contoh.com", nama_batch="UAS Fisika", status=StatusBatch.SELESAI
    )
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Citra", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal, skor_sistem=92, skor_revisi=95)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    wb = _baca_xlsx(response.content)
    assert wb["sheet_names"] == ["Rekap Nilai"]
    assert _nilai_sel(wb, "B3") == "Citra"
    assert _nilai_sel(wb, "C3") == "Selesai"
    assert _nilai_sel(wb, "D3") == 92
    assert _nilai_sel(wb, "E3") == "Sangat Mirip"
    assert _nilai_sel(wb, "F3") == 95
    assert _nilai_sel(wb, "G3") == 95


async def test_ekspor_batch_tanpa_jawaban_ditolak_400(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch_tanpa_soal = await _buat_batch(db_session, "pro@contoh.com", nama_batch="Baru")
    id_batch_dengan_soal = await _buat_batch(db_session, "pro@contoh.com", nama_batch="Ada Soal")
    await _tambah_soal_db(db_session, id_batch_dengan_soal, 1)

    for id_batch in (id_batch_tanpa_soal, id_batch_dengan_soal):
        response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))
        assert response.status_code == 400
        assert response.json() == {
            "kode": "BATCH_BELUM_ADA_JAWABAN",
            "pesan": "Belum ada jawaban peserta didik pada batch ini untuk diekspor.",
        }


async def test_ekspor_struktur_isi_urutan_nilai_akhir_kosong_dan_rata_rata(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com", nama_batch="UTS Matematika")

    # Sisipkan soal dalam urutan tidak berurutan untuk memastikan ekspor mengurutkan no_soal ASC.
    id_soal_3 = await _tambah_soal_db(db_session, id_batch, 3, "Kunci 3")
    id_soal_1 = await _tambah_soal_db(db_session, id_batch, 1, "Kunci 1")
    id_soal_2 = await _tambah_soal_db(db_session, id_batch, 2, "Kunci 2")

    waktu = datetime(2026, 11, 22, 8, 0, 0, tzinfo=UTC)
    id_kecil = uuid.UUID("00000000-0000-0000-0000-000000000001")
    id_besar = uuid.UUID("00000000-0000-0000-0000-000000000002")

    # Peserta 1 & 2 memiliki diunggah_pada identik: tie-breaker harus urut id_file ASC.
    p2 = await _buat_file(
        db_session, id_batch, "Budi", StatusProses.SELESAI, diunggah_pada=waktu, id_file=id_besar
    )
    p1 = await _buat_file(
        db_session, id_batch, "Andi", StatusProses.SELESAI, diunggah_pada=waktu, id_file=id_kecil
    )
    p3 = await _buat_file(
        db_session,
        id_batch,
        "Citra",
        StatusProses.SELESAI,
        diunggah_pada=waktu + timedelta(seconds=5),
    )

    # Andi: Soal 1 (80, belum revisi), Soal 2 (60, revisi 90), Soal 3 (0, belum revisi)
    # Rata-rata = (80 + 90 + 0) / 3 = 56.67
    await _buat_hasil(db_session, p1.id_file, id_soal_1, 80, Kategori.SANGAT_MIRIP, None)
    await _buat_hasil(db_session, p1.id_file, id_soal_2, 60, Kategori.CUKUP_MIRIP, 90)
    await _buat_hasil(db_session, p1.id_file, id_soal_3, 0, Kategori.KURANG_MIRIP, None)

    # Budi: Soal 1 (85, revisi 0 -> pakai 0!), Soal 2 (100, belum revisi), Soal 3 (None, None)
    # Rata-rata = (0 + 100) / 2 = 50
    await _buat_hasil(db_session, p2.id_file, id_soal_1, 85, Kategori.SANGAT_MIRIP, 0)
    await _buat_hasil(db_session, p2.id_file, id_soal_2, 100, Kategori.SANGAT_MIRIP, None)
    await _buat_hasil(db_session, p2.id_file, id_soal_3, None, None, None)

    # Citra: semua skor None -> Rata-rata kosong
    await _buat_hasil(db_session, p3.id_file, id_soal_1, None, None, None)
    await _buat_hasil(db_session, p3.id_file, id_soal_2, None, None, None)
    await _buat_hasil(db_session, p3.id_file, id_soal_3, None, None, None)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    wb = _baca_xlsx(response.content)

    assert wb["sheet_names"] == ["Rekap Nilai"]
    assert wb["formula_cells"] == []
    assert wb["merges"] == {
        "A1:A2",
        "B1:B2",
        "C1:C2",
        "D1:F1",
        "G1:I1",
        "J1:L1",
        "M1:M2",
    }

    # Header baris 1 & 2
    assert _nilai_sel(wb, "A1") == "No"
    assert _nilai_sel(wb, "B1") == "Nama Peserta Didik"
    assert _nilai_sel(wb, "C1") == "Status"
    assert _nilai_sel(wb, "D1") == "Soal 1"
    assert _nilai_sel(wb, "G1") == "Soal 2"
    assert _nilai_sel(wb, "J1") == "Soal 3"
    assert _nilai_sel(wb, "M1") == "Rata-rata"
    for col_skor, col_kat, col_akhir in (("D", "E", "F"), ("G", "H", "I"), ("J", "K", "L")):
        assert _nilai_sel(wb, f"{col_skor}2") == "Skor"
        assert _nilai_sel(wb, f"{col_kat}2") == "Kategori"
        assert _nilai_sel(wb, f"{col_akhir}2") == "Nilai Akhir"

    # Baris 3: Andi
    assert _nilai_sel(wb, "A3") == 1
    assert _nilai_sel(wb, "B3") == "Andi"
    assert _nilai_sel(wb, "C3") == "Selesai"
    assert _nilai_sel(wb, "D3") == 80
    assert _nilai_sel(wb, "E3") == "Sangat Mirip"
    assert _nilai_sel(wb, "F3") is None  # Nilai Akhir kosong bila belum direvisi
    assert _nilai_sel(wb, "G3") == 60
    assert _nilai_sel(wb, "H3") == "Cukup Mirip"
    assert _nilai_sel(wb, "I3") == 90
    assert _nilai_sel(wb, "J3") == 0  # Skor 0 bukan kosong
    assert _nilai_sel(wb, "K3") == "Kurang Mirip"
    assert _nilai_sel(wb, "L3") is None
    assert _nilai_sel(wb, "M3") == 56.67

    # Baris 4: Budi
    assert _nilai_sel(wb, "A4") == 2
    assert _nilai_sel(wb, "B4") == "Budi"
    assert _nilai_sel(wb, "C4") == "Selesai"
    assert _nilai_sel(wb, "D4") == 85
    assert _nilai_sel(wb, "E4") == "Sangat Mirip"
    assert _nilai_sel(wb, "F4") == 0  # Nilai Akhir 0 sah & dipakai untuk Rata-rata
    assert _nilai_sel(wb, "G4") == 100
    assert _nilai_sel(wb, "H4") == "Sangat Mirip"
    assert _nilai_sel(wb, "I4") is None
    assert _nilai_sel(wb, "J4") is None
    assert _nilai_sel(wb, "K4") is None
    assert _nilai_sel(wb, "L4") is None
    assert _nilai_sel(wb, "M4") == 50

    # Baris 5: Citra (semua skor kosong -> Rata-rata kosong)
    assert _nilai_sel(wb, "A5") == 3
    assert _nilai_sel(wb, "B5") == "Citra"
    assert _nilai_sel(wb, "C5") == "Selesai"
    assert _nilai_sel(wb, "M5") is None


async def test_ekspor_baris_diproses_dan_gagal_sel_nilai_kosong(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)

    waktu = datetime(2026, 11, 22, 8, 0, 0, tzinfo=UTC)
    f_selesai = await _buat_file(db_session, id_batch, "Selesai Siswa", StatusProses.SELESAI, waktu)
    f_diproses = await _buat_file(
        db_session, id_batch, "Diproses Siswa", StatusProses.DIPROSES, waktu + timedelta(seconds=1)
    )
    f_gagal = await _buat_file(
        db_session, id_batch, "Gagal Siswa", StatusProses.GAGAL, waktu + timedelta(seconds=2)
    )

    await _buat_hasil(db_session, f_selesai.id_file, id_soal, 88, Kategori.SANGAT_MIRIP, None)
    # Simulasikan baris Hasil_Koreksi sisa (mis. Coba Lagi atau OCR sukses lalu judge gagal):
    # baris Diproses dan Gagal tetap HARUS kosong seluruh sel nilainya.
    await _buat_hasil(db_session, f_diproses.id_file, id_soal, 70, Kategori.CUKUP_MIRIP, 75)
    await _buat_hasil(db_session, f_gagal.id_file, id_soal, None, None, 60)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    wb = _baca_xlsx(response.content)

    # Baris 3: Selesai
    assert _nilai_sel(wb, "B3") == "Selesai Siswa"
    assert _nilai_sel(wb, "C3") == "Selesai"
    assert _nilai_sel(wb, "D3") == 88
    assert _nilai_sel(wb, "G3") == 88

    # Baris 4: Diproses -> semua sel nilai & Rata-rata kosong
    assert _nilai_sel(wb, "A4") == 2
    assert _nilai_sel(wb, "B4") == "Diproses Siswa"
    assert _nilai_sel(wb, "C4") == "Diproses"
    for col in ("D", "E", "F", "G"):
        assert _nilai_sel(wb, f"{col}4") is None

    # Baris 5: Gagal -> semua sel nilai & Rata-rata kosong
    assert _nilai_sel(wb, "A5") == 3
    assert _nilai_sel(wb, "B5") == "Gagal Siswa"
    assert _nilai_sel(wb, "C5") == "Gagal"
    for col in ("D", "E", "F", "G"):
        assert _nilai_sel(wb, f"{col}5") is None


async def test_ekspor_nama_peserta_kosong_atau_none(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Kasus tepi: nama_peserta_didik kosong (di DB) atau None (di dataclass)
    tidak menyebabkan galat dan ditulis kosong seperti tampilan daftar di UI."""
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com")
    await _tambah_soal_db(db_session, id_batch, 1)
    await _buat_file(db_session, id_batch, "", StatusProses.GAGAL)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    wb = _baca_xlsx(response.content)
    assert _nilai_sel(wb, "A3") == 1
    assert _nilai_sel(wb, "B3") is None
    assert _nilai_sel(wb, "C3") == "Gagal"

    # Uji langsung nilai None pada pembangun workbook.
    konten_none = ekspor_service._bangun_workbook_bytes(
        ekspor_service.DataEkspor(
            nama_batch="Uji None",
            daftar_no_soal=(1,),
            baris_peserta=(
                ekspor_service.BarisPesertaEkspor(
                    nama_peserta_didik=None,
                    status_proses=StatusProses.GAGAL,
                    nilai_per_soal=(None,),
                ),
            ),
        )
    )
    wb_none = _baca_xlsx(konten_none)
    assert _nilai_sel(wb_none, "B3") is None
    assert _nilai_sel(wb_none, "C3") == "Gagal"


async def test_ekspor_selesai_tanpa_baris_hasil_koreksi_pada_soal_tertentu(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Kasus tepi: peserta Selesai tidak punya baris Hasil_Koreksi untuk Soal 2
    -> sel Soal 2 kosong, tanpa galat, dan Rata-rata hanya menghitung Soal 1 & 3."""
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com")
    id_soal_1 = await _tambah_soal_db(db_session, id_batch, 1)
    await _tambah_soal_db(db_session, id_batch, 2)  # sengaja tidak punya HasilKoreksi
    id_soal_3 = await _tambah_soal_db(db_session, id_batch, 3)

    fj = await _buat_file(db_session, id_batch, "Dina", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal_1, 80, Kategori.SANGAT_MIRIP, None)
    await _buat_hasil(db_session, fj.id_file, id_soal_3, 90, Kategori.SANGAT_MIRIP, None)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    wb = _baca_xlsx(response.content)
    assert _nilai_sel(wb, "B3") == "Dina"
    assert _nilai_sel(wb, "D3") == 80
    assert _nilai_sel(wb, "E3") == "Sangat Mirip"
    assert _nilai_sel(wb, "F3") is None
    # Soal 2 (kolom G, H, I) kosong seluruhnya
    assert _nilai_sel(wb, "G3") is None
    assert _nilai_sel(wb, "H3") is None
    assert _nilai_sel(wb, "I3") is None
    # Soal 3 (kolom J, K, L)
    assert _nilai_sel(wb, "J3") == 90
    assert _nilai_sel(wb, "K3") == "Sangat Mirip"
    assert _nilai_sel(wb, "L3") is None
    # Rata-rata hanya dari Soal 1 & 3: (80 + 90) / 2 = 85
    assert _nilai_sel(wb, "M3") == 85


async def test_ekspor_proteksi_injeksi_formula(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com", nama_batch="=SUM(1,1)")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)

    nama_berbahaya = [
        "=SUM(1,1)",
        "+cmd|' /C calc'!A0",
        "-2+3",
        "@SUM(A1:A2)",
        ' =HYPERLINK("http://contoh.com")',
        "\t=1+1",
    ]
    waktu = datetime(2026, 11, 22, 8, 0, 0, tzinfo=UTC)
    for i, nama in enumerate([*nama_berbahaya, "Budi Santoso"]):
        fj = await _buat_file(
            db_session, id_batch, nama, StatusProses.SELESAI, waktu + timedelta(seconds=i)
        )
        await _buat_hasil(db_session, fj.id_file, id_soal, 80, Kategori.SANGAT_MIRIP, None)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    wb = _baca_xlsx(response.content)
    assert wb["formula_cells"] == []

    for i, nama in enumerate(nama_berbahaya):
        sel = wb["cells"][f"B{3 + i}"]
        assert sel["type"] == "s"
        assert sel["value"] == nama
        assert sel["quote_prefix"] is True

    sel_normal = wb["cells"][f"B{3 + len(nama_berbahaya)}"]
    assert sel_normal["type"] == "s"
    assert sel_normal["value"] == "Budi Santoso"
    assert sel_normal["quote_prefix"] is False


async def test_ekspor_sanitasi_nama_file_dan_header(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(
        db_session, "pro@contoh.com", nama_batch='UTS: IPA/IPS *2026* "?<>|=+-@'
    )
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 200
    cd = response.headers["content-disposition"]
    assert re.fullmatch(
        r'attachment; filename="rekap-nilai-uts-ipa-ips-2026-\d{4}-\d{2}-\d{2}\.xlsx"',
        cd,
    ), f"Content-Disposition tidak sesuai: {cd!r}"

    # Uji langsung fungsi murni untuk kasus ekstrem.
    tgl = date(2026, 11, 22)
    assert ekspor_service.buat_nama_file_ekspor("///:::**???", tgl) == (
        "rekap-nilai-batch-2026-11-22.xlsx"
    )
    assert ekspor_service.buat_nama_file_ekspor("Évaluasi Bahasa", tgl) == (
        "rekap-nilai-evaluasi-bahasa-2026-11-22.xlsx"
    )
    nama_panjang = "a" * 100
    hasil_panjang = ekspor_service.buat_nama_file_ekspor(nama_panjang, tgl)
    assert hasil_panjang == f"rekap-nilai-{'a' * 80}-2026-11-22.xlsx"


async def test_ekspor_gagal_buat_workbook_500(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
) -> None:
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal)

    def _meledak(_data):
        raise RuntimeError("detail internal rahasia")

    monkeypatch.setattr(ekspor_service, "_bangun_workbook_bytes", _meledak)

    response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))

    assert response.status_code == 500
    assert response.json() == {
        "kode": "GAGAL_EKSPOR",
        "pesan": "Gagal membuat file ekspor, silakan coba lagi",
    }
    assert "rahasia" not in response.text


async def test_ekspor_aman_terhadap_session_expire_setelah_rollback(
    _engine, client: AsyncClient, db_session: AsyncSession
) -> None:
    """Pastikan tidak ada akses atribut ORM setelah await db.rollback()
    sekalipun session memakai expire_on_commit=True."""
    token = await _token_pro(client, db_session)
    id_batch = await _buat_batch(db_session, "pro@contoh.com", nama_batch="Batch Strict")
    id_soal = await _tambah_soal_db(db_session, id_batch, 1)
    fj = await _buat_file(db_session, id_batch, "Andi", StatusProses.SELESAI)
    await _buat_hasil(db_session, fj.id_file, id_soal, 88, Kategori.SANGAT_MIRIP, None)

    strict_maker = async_sessionmaker(_engine, expire_on_commit=True)

    async def _override_strict_db():
        async with strict_maker() as sesi_ketat:
            yield sesi_ketat

    sebelumnya = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_strict_db
    try:
        response = await client.get(f"/api/batch/{id_batch}/ekspor", headers=_auth(token))
    finally:
        if sebelumnya is not None:
            app.dependency_overrides[get_db] = sebelumnya
        else:
            app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert "rekap-nilai-batch-strict-" in response.headers["content-disposition"]
