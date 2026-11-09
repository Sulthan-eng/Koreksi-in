"""Satu-satunya modul yang mengirim email (SPEC bagian 9, F-RESET).

Memakai smtplib (stdlib) dengan STARTTLS, dibungkus asyncio.to_thread agar
tidak memblokir event loop. Tidak ada dependency baru. Token TIDAK PERNAH
dicatat di log.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _buat_pesan_reset(email_tujuan: str, token: str) -> EmailMessage:
    tautan = f"{settings.FRONTEND_URL}/atur-ulang-password?token={token}"
    pesan = EmailMessage()
    pesan["Subject"] = "Atur ulang password Koreksi-in"
    pesan["From"] = f"Koreksi-in <{settings.SMTP_USER}>"
    pesan["To"] = email_tujuan
    pesan.set_content(
        "Anda meminta atur ulang password Koreksi-in.\n\n"
        f"Buka tautan berikut untuk mengatur password baru: {tautan}\n\n"
        "Tautan ini berlaku selama 30 menit.\n"
        "Jika Anda tidak meminta ini, abaikan email ini."
    )
    return pesan


def _kirim_smtp(pesan: EmailMessage) -> None:
    """Satu-satunya titik panggilan jaringan SMTP; dimock di test."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(pesan)


async def kirim_email_reset_password(email_tujuan: str, token: str) -> None:
    """Dipanggil lewat BackgroundTasks. Kegagalan (termasuk SMTP_USER/PASSWORD
    kosong) hanya dicatat log, tidak dilempar."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("kirim_email_reset_password_gagal alasan=kredensial_smtp_kosong")
        return

    pesan = _buat_pesan_reset(email_tujuan, token)
    try:
        await asyncio.to_thread(_kirim_smtp, pesan)
    except Exception:
        logger.error("kirim_email_reset_password_gagal", exc_info=True)
