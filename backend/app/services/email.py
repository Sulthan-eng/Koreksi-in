"""Satu-satunya modul yang mengirim email (SPEC bagian 9, F-RESET; FR30).

Memakai smtplib (stdlib) dengan STARTTLS, dibungkus asyncio.to_thread agar
tidak memblokir event loop. Tidak ada dependency baru. Token, tautan reset,
dan alamat email TIDAK PERNAH dicatat di log. Isi (subjek/HTML/teks) email
FR30 ada di app/services/email_templates.py, modul ini hanya memasangnya
ke EmailMessage dan mengirim.
"""

import asyncio
import logging
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from app.core.config import settings
from app.services import email_templates

logger = logging.getLogger(__name__)


def _buat_pesan_reset(email_tujuan: str, token: str) -> EmailMessage:
    tautan = f"{settings.FRONTEND_URL.rstrip('/')}/atur-ulang-password?token={token}"
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
        server.starttls(context=ssl.create_default_context())
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(pesan)


async def kirim_email_reset_password(email_tujuan: str, token: str) -> None:
    """Dipanggil lewat BackgroundTasks. Kegagalan (termasuk SMTP_USER/PASSWORD
    kosong) hanya dicatat log, tidak dilempar."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("kirim_email_reset_password_gagal alasan=kredensial_smtp_kosong")
        return

    pesan = _buat_pesan_reset(email_tujuan, token)
    await _kirim_dan_catat_gagal(pesan, "kirim_email_reset_password_gagal")


def _buat_pesan_html(email_tujuan: str, isi: email_templates.IsiEmail) -> EmailMessage:
    pesan = EmailMessage()
    pesan["Subject"] = isi.subjek
    pesan["From"] = f"Koreksi-in <{settings.SMTP_USER}>"
    pesan["To"] = email_tujuan
    pesan.set_content(isi.teks)
    pesan.add_alternative(isi.html, subtype="html")
    return pesan


async def _kirim_dan_catat_gagal(pesan: EmailMessage, label_log: str) -> None:
    try:
        await asyncio.to_thread(_kirim_smtp, pesan)
    except Exception as exc:
        # Catat metadata aman saja (tanpa exc_info/str(exc)): SMTPRecipientsRefused
        # dan SMTPSenderRefused memuat alamat email pada representasi error-nya.
        kode = getattr(exc, "smtp_code", None)
        logger.error("%s tipe=%s kode=%s", label_log, type(exc).__name__, kode)


async def kirim_email_pembayaran_berhasil(
    email_tujuan: str,
    nama: str,
    nomor_invoice: str,
    nama_paket: str,
    nominal: int,
    dibayar_pada: datetime,
) -> None:
    """Dipanggil lewat BackgroundTasks setelah status transaksi Berhasil
    di-commit (FR30). Kegagalan hanya dicatat log, tidak dilempar."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("kirim_email_pembayaran_berhasil_gagal alasan=kredensial_smtp_kosong")
        return

    url_dasar = settings.FRONTEND_URL.rstrip("/")
    tautan_invoice = f"{url_dasar}/invoice/{nomor_invoice}"
    isi = email_templates.email_pembayaran_berhasil(
        nama=nama,
        nomor_invoice=nomor_invoice,
        nama_paket=nama_paket,
        nominal=nominal,
        dibayar_pada=dibayar_pada,
        tautan_invoice=tautan_invoice,
        frontend_url=url_dasar,
    )
    pesan = _buat_pesan_html(email_tujuan, isi)
    await _kirim_dan_catat_gagal(pesan, "kirim_email_pembayaran_berhasil_gagal")


async def kirim_email_pembayaran_kedaluwarsa(
    email_tujuan: str, nama: str, nomor_invoice: str, nama_paket: str, nominal: int
) -> None:
    """Dipanggil lewat BackgroundTasks setelah status transaksi Kedaluwarsa
    di-commit (FR30). Kegagalan hanya dicatat log, tidak dilempar."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("kirim_email_pembayaran_kedaluwarsa_gagal alasan=kredensial_smtp_kosong")
        return

    url_dasar = settings.FRONTEND_URL.rstrip("/")
    tautan_langganan = f"{url_dasar}/langganan"
    isi = email_templates.email_pembayaran_kedaluwarsa(
        nama=nama,
        nomor_invoice=nomor_invoice,
        nama_paket=nama_paket,
        nominal=nominal,
        tautan_langganan=tautan_langganan,
        frontend_url=url_dasar,
    )
    pesan = _buat_pesan_html(email_tujuan, isi)
    await _kirim_dan_catat_gagal(pesan, "kirim_email_pembayaran_kedaluwarsa_gagal")
