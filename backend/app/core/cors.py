"""Satu sumber kebenaran untuk daftar origin yang diizinkan.

Dipakai dua tempat yang tidak bisa saling menggantikan:

1. CORSMiddleware di main.py, untuk request dan preflight biasa.
2. unexpected_error_handler di errors.py. Handler Exception dipasang Starlette di
   ServerErrorMiddleware, yang berada DI LUAR middleware pengguna, jadi respons 500
   tak terduga tidak pernah melewati CORSMiddleware. Tanpa header dari sini, browser
   hanya melihat "network error", bukan pesan galat aplikasi.

Keduanya memanggil fungsi di modul ini agar daftarnya tidak bisa tidak sinkron.
"""

from urllib.parse import urlsplit

from app.core.config import settings

ORIGIN_DEV = "http://localhost:5173"


def origin_dari_url(url: str) -> str:
    """Ambil origin (scheme://host[:port]) dari sebuah URL, tanpa path dan trailing slash."""
    bagian = urlsplit(url.strip())
    if not bagian.scheme or not bagian.netloc:
        raise ValueError(f"URL tidak memuat scheme dan host: {url!r}")
    return f"{bagian.scheme}://{bagian.netloc}"


def asal_diizinkan() -> list[str]:
    """Origin frontend dari FRONTEND_URL, ditambah origin dev di luar produksi."""
    daftar = [origin_dari_url(settings.FRONTEND_URL)]
    if settings.ENV != "produksi" and ORIGIN_DEV not in daftar:
        daftar.append(ORIGIN_DEV)
    return daftar


def header_cors(origin: str | None) -> dict[str, str]:
    """Header CORS minimal untuk respons galat (bukan preflight), kosong bila origin ditolak."""
    if origin is None or origin not in asal_diizinkan():
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
