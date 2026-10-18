from io import BytesIO

from pypdf import PdfReader


def hitung_halaman(konten: bytes, ext: str) -> int:
    """Jumlah halaman berkas. Gambar selalu 1 halaman."""
    if ext != "pdf":
        return 1
    return len(PdfReader(BytesIO(konten)).pages)
