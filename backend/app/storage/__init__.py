from functools import lru_cache

from app.core.config import settings
from app.storage.basis import GAGAL_AKSES_PENYIMPANAN, PenyimpananBerkas
from app.storage.lokal import StorageLokal
from app.storage.s3 import StorageS3

__all__ = ["GAGAL_AKSES_PENYIMPANAN", "PenyimpananBerkas", "dapatkan_storage"]


@lru_cache(maxsize=1)
def dapatkan_storage() -> PenyimpananBerkas:
    if settings.STORAGE_BACKEND == "s3":
        return StorageS3()
    return StorageLokal()
