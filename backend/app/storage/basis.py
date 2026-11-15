from typing import Protocol

from app.core.errors import AppError

GAGAL_AKSES_PENYIMPANAN = AppError(
    kode="GAGAL_AKSES_PENYIMPANAN",
    pesan="Gagal mengakses penyimpanan berkas, silakan coba lagi.",
    status_code=500,
)


class PenyimpananBerkas(Protocol):
    """Lapisan abstraksi penyimpanan berkas jawaban. Semua operasi async;
    implementasi membungkus client sync dengan asyncio.to_thread di dalam,
    bukan di pemanggil. Kegagalan I/O dipetakan ke GAGAL_AKSES_PENYIMPANAN."""

    async def simpan(self, kunci: str, konten: bytes) -> None: ...

    async def baca(self, kunci: str) -> bytes: ...

    async def hapus(self, kunci: str) -> None: ...

    async def hapus_prefix(self, prefix: str) -> None: ...


def validasi_prefix(prefix: str) -> None:
    """Dipanggil di awal hapus_prefix kedua implementasi. ValueError (bug
    pemanggil, bukan AppError) bila prefix kosong atau tidak diakhiri '/' —
    mencegah "uploads/1" ikut mencocokkan "uploads/10/..."."""
    if not prefix or not prefix.endswith("/"):
        raise ValueError(f"prefix harus diakhiri '/' dan tidak boleh kosong: {prefix!r}")
