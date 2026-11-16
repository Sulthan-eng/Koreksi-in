import io

import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from app.core.config import settings
from app.storage.basis import GAGAL_AKSES_PENYIMPANAN
from app.storage.lokal import StorageLokal
from app.storage.s3 import StorageS3


@pytest.fixture(autouse=True)
def _upload_dir_sementara(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))


class TestStorageLokal:
    async def test_simpan_menulis_isi_dan_membuat_subdirektori(self, tmp_path):
        storage = StorageLokal()
        await storage.simpan("uploads/1/a.png", b"konten")
        assert (tmp_path / "uploads" / "1" / "a.png").read_bytes() == b"konten"

    async def test_baca_mengembalikan_isi_sama(self, tmp_path):
        storage = StorageLokal()
        await storage.simpan("uploads/1/a.png", b"isi-asli")
        assert await storage.baca("uploads/1/a.png") == b"isi-asli"

    async def test_baca_kunci_tak_ada_melempar_gagal_akses(self):
        storage = StorageLokal()
        with pytest.raises(type(GAGAL_AKSES_PENYIMPANAN)) as exc_info:
            await storage.baca("uploads/tak-ada/a.png")
        assert exc_info.value.kode == "GAGAL_AKSES_PENYIMPANAN"

    async def test_hapus_kunci_ada_menghapus_berkas(self, tmp_path):
        storage = StorageLokal()
        await storage.simpan("uploads/1/a.png", b"x")
        await storage.hapus("uploads/1/a.png")
        assert not (tmp_path / "uploads" / "1" / "a.png").exists()

    async def test_hapus_kunci_tak_ada_tidak_error(self):
        storage = StorageLokal()
        await storage.hapus("uploads/tak-ada/a.png")

    async def test_hapus_prefix_menghapus_seluruh_isi_rekursif(self, tmp_path):
        storage = StorageLokal()
        await storage.simpan("uploads/1/a.png", b"x")
        await storage.simpan("uploads/1/b.png", b"y")
        await storage.hapus_prefix("uploads/1/")
        assert not (tmp_path / "uploads" / "1").exists()

    async def test_hapus_prefix_direktori_tak_ada_tidak_error(self):
        storage = StorageLokal()
        await storage.hapus_prefix("uploads/tak-ada/")

    async def test_hapus_prefix_kosong_atau_tanpa_trailing_slash_ditolak(self):
        storage = StorageLokal()
        with pytest.raises(ValueError):
            await storage.hapus_prefix("")
        with pytest.raises(ValueError):
            await storage.hapus_prefix("uploads/1")

    async def test_hapus_prefix_tidak_menyentuh_batch_lain(self, tmp_path):
        storage = StorageLokal()
        await storage.simpan("uploads/1/a.png", b"x")
        await storage.simpan("uploads/10/b.png", b"y")
        await storage.hapus_prefix("uploads/1/")
        assert not (tmp_path / "uploads" / "1").exists()
        assert (tmp_path / "uploads" / "10" / "b.png").read_bytes() == b"y"


@pytest.fixture
def _storage_s3(monkeypatch):
    monkeypatch.setattr(settings, "S3_ENDPOINT_URL", "https://contoh.supabase.co/storage/v1/s3")
    monkeypatch.setattr(settings, "S3_REGION", "ap-southeast-1")
    monkeypatch.setattr(settings, "S3_BUCKET", "jawaban")
    monkeypatch.setattr(settings, "S3_ACCESS_KEY_ID", "testing")
    monkeypatch.setattr(settings, "S3_SECRET_ACCESS_KEY", "testing")
    storage = StorageS3()
    stubber = Stubber(storage._client)
    stubber.activate()
    yield storage, stubber
    stubber.assert_no_pending_responses()
    stubber.deactivate()


class TestStorageS3:
    async def test_simpan_mengirim_bucket_key_body(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_response(
            "put_object",
            {},
            {"Bucket": "jawaban", "Key": "uploads/1/a.png", "Body": b"konten"},
        )
        await storage.simpan("uploads/1/a.png", b"konten")

    async def test_baca_mengembalikan_isi_body(self, _storage_s3):
        storage, stubber = _storage_s3
        body = StreamingBody(io.BytesIO(b"isi-s3"), content_length=len(b"isi-s3"))
        stubber.add_response(
            "get_object",
            {"Body": body},
            {"Bucket": "jawaban", "Key": "uploads/1/a.png"},
        )
        assert await storage.baca("uploads/1/a.png") == b"isi-s3"

    async def test_baca_kunci_tak_ada_melempar_gagal_akses(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_client_error(
            "get_object",
            service_error_code="NoSuchKey",
            expected_params={"Bucket": "jawaban", "Key": "uploads/tak-ada/a.png"},
        )
        with pytest.raises(type(GAGAL_AKSES_PENYIMPANAN)) as exc_info:
            await storage.baca("uploads/tak-ada/a.png")
        assert exc_info.value.kode == "GAGAL_AKSES_PENYIMPANAN"

    async def test_hapus_mengirim_bucket_key(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_response("delete_object", {}, {"Bucket": "jawaban", "Key": "uploads/1/a.png"})
        await storage.hapus("uploads/1/a.png")

    async def test_hapus_prefix_list_lalu_hapus_tiap_key(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_response(
            "list_objects_v2",
            {
                "Contents": [{"Key": "uploads/1/a.png"}, {"Key": "uploads/1/b.png"}],
                "IsTruncated": False,
            },
            {"Bucket": "jawaban", "Prefix": "uploads/1/"},
        )
        stubber.add_response("delete_object", {}, {"Bucket": "jawaban", "Key": "uploads/1/a.png"})
        stubber.add_response("delete_object", {}, {"Bucket": "jawaban", "Key": "uploads/1/b.png"})
        await storage.hapus_prefix("uploads/1/")

    async def test_hapus_prefix_kosong_tidak_memanggil_delete(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_response(
            "list_objects_v2",
            {"Contents": [], "IsTruncated": False},
            {"Bucket": "jawaban", "Prefix": "uploads/1/"},
        )
        await storage.hapus_prefix("uploads/1/")

    async def test_hapus_prefix_hanya_mengirim_prefix_batch_yang_dituju(self, _storage_s3):
        storage, stubber = _storage_s3
        stubber.add_response(
            "list_objects_v2",
            {"Contents": [{"Key": "uploads/1/a.png"}], "IsTruncated": False},
            {"Bucket": "jawaban", "Prefix": "uploads/1/"},
        )
        stubber.add_response("delete_object", {}, {"Bucket": "jawaban", "Key": "uploads/1/a.png"})
        await storage.hapus_prefix("uploads/1/")

    async def test_hapus_prefix_kosong_atau_tanpa_trailing_slash_ditolak(self, _storage_s3):
        storage, _stubber = _storage_s3
        with pytest.raises(ValueError):
            await storage.hapus_prefix("")
        with pytest.raises(ValueError):
            await storage.hapus_prefix("uploads/1")
