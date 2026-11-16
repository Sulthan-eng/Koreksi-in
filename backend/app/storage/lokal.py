import asyncio
import shutil
from pathlib import Path

from app.core.config import settings
from app.storage.basis import GAGAL_AKSES_PENYIMPANAN, validasi_prefix


class StorageLokal:
    """Implementasi berbasis UPLOAD_DIR. Dipakai dev dan test (default)."""

    def _basis(self) -> Path:
        # Dibaca ulang tiap panggilan (tidak di-cache) agar fixture test yang
        # memonkeypatch settings.UPLOAD_DIR tetap bekerja.
        return Path(settings.UPLOAD_DIR)

    def _tulis(self, path: Path, konten: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(konten)

    async def simpan(self, kunci: str, konten: bytes) -> None:
        try:
            await asyncio.to_thread(self._tulis, self._basis() / kunci, konten)
        except OSError:
            raise GAGAL_AKSES_PENYIMPANAN from None

    async def baca(self, kunci: str) -> bytes:
        try:
            return await asyncio.to_thread((self._basis() / kunci).read_bytes)
        except OSError:
            raise GAGAL_AKSES_PENYIMPANAN from None

    async def hapus(self, kunci: str) -> None:
        try:
            await asyncio.to_thread((self._basis() / kunci).unlink, True)
        except OSError:
            raise GAGAL_AKSES_PENYIMPANAN from None

    def _hapus_direktori(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)

    async def hapus_prefix(self, prefix: str) -> None:
        validasi_prefix(prefix)
        try:
            await asyncio.to_thread(self._hapus_direktori, self._basis() / prefix)
        except OSError:
            raise GAGAL_AKSES_PENYIMPANAN from None
