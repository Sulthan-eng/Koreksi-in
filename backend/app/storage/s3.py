import asyncio
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.storage.basis import GAGAL_AKSES_PENYIMPANAN, validasi_prefix

logger = logging.getLogger(__name__)

# Backend satu instance/satu worker (SPEC U13): panggilan storage yang
# menggantung lama memblokir satu-satunya worker, jadi timeout harus pendek.
# addressing_style "path" dan checksum "when_required" untuk kompatibilitas
# dengan S3-compatible provider pihak ketiga (Supabase Storage), bukan AWS asli.
_KONFIG_KLIEN = Config(
    connect_timeout=5,
    read_timeout=15,
    retries={"max_attempts": 2, "mode": "standard"},
    s3={"addressing_style": "path"},
    request_checksum_calculation="when_required",
    response_checksum_validation="when_required",
)


def _kode_galat(exc: Exception) -> str | None:
    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code")
    return None


class StorageS3:
    """Implementasi berbasis S3-compatible API (Supabase Storage).
    Satu-satunya modul yang mengimpor boto3."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            config=_KONFIG_KLIEN,
        )
        self._bucket = settings.S3_BUCKET

    def _simpan(self, kunci: str, konten: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=kunci, Body=konten)

    async def simpan(self, kunci: str, konten: bytes) -> None:
        try:
            await asyncio.to_thread(self._simpan, kunci, konten)
        except (ClientError, BotoCoreError) as exc:
            logger.error(
                "storage_s3_gagal operasi=simpan kunci=%s kode=%s", kunci, _kode_galat(exc)
            )
            raise GAGAL_AKSES_PENYIMPANAN from None

    def _baca(self, kunci: str) -> bytes:
        return self._client.get_object(Bucket=self._bucket, Key=kunci)["Body"].read()

    async def baca(self, kunci: str) -> bytes:
        try:
            return await asyncio.to_thread(self._baca, kunci)
        except (ClientError, BotoCoreError) as exc:
            logger.error("storage_s3_gagal operasi=baca kunci=%s kode=%s", kunci, _kode_galat(exc))
            raise GAGAL_AKSES_PENYIMPANAN from None

    def _hapus(self, kunci: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=kunci)

    async def hapus(self, kunci: str) -> None:
        try:
            await asyncio.to_thread(self._hapus, kunci)
        except (ClientError, BotoCoreError) as exc:
            logger.error("storage_s3_gagal operasi=hapus kunci=%s kode=%s", kunci, _kode_galat(exc))
            raise GAGAL_AKSES_PENYIMPANAN from None

    def _hapus_prefix(self, prefix: str) -> None:
        paginator = self._client.get_paginator("list_objects_v2")
        for halaman in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for objek in halaman.get("Contents", []):
                self._client.delete_object(Bucket=self._bucket, Key=objek["Key"])

    async def hapus_prefix(self, prefix: str) -> None:
        validasi_prefix(prefix)
        try:
            await asyncio.to_thread(self._hapus_prefix, prefix)
        except (ClientError, BotoCoreError) as exc:
            logger.error(
                "storage_s3_gagal operasi=hapus_prefix kunci=%s kode=%s", prefix, _kode_galat(exc)
            )
            raise GAGAL_AKSES_PENYIMPANAN from None
