import logging
import smtplib

import pytest

from app.core.config import settings
from app.services import email as email_service


@pytest.mark.parametrize(
    "buat_exc,tipe_harapan,kode_harapan",
    [
        (
            lambda email, pengirim, token: OSError(
                f"gagal konek untuk {email} tautan=http://localhost:5173/atur-ulang-password?token={token}"
            ),
            "OSError",
            "None",
        ),
        (
            lambda email, pengirim, token: smtplib.SMTPRecipientsRefused(
                {email: (550, b"5.1.1 User unknown")}
            ),
            "SMTPRecipientsRefused",
            "None",
        ),
        (
            lambda email, pengirim, token: smtplib.SMTPSenderRefused(
                550, b"5.7.1 Sender rejected", pengirim
            ),
            "SMTPSenderRefused",
            "550",
        ),
        (
            lambda email, pengirim, token: smtplib.SMTPAuthenticationError(
                535, b"5.7.8 Authentication failed"
            ),
            "SMTPAuthenticationError",
            "535",
        ),
    ],
    ids=["oserror_dengan_tautan", "recipients_refused", "sender_refused", "auth_error"],
)
async def test_kirim_email_reset_tidak_bocor_token_tautan_atau_email_ke_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    buat_exc,
    tipe_harapan: str,
    kode_harapan: str,
) -> None:
    email_pengirim = "pengirim@contoh.com"
    email_tujuan = "budi@contoh.com"
    password_smtp = "rahasia-app-password"
    token_rahasia = "token-rahasia-tidak-boleh-bocor"

    monkeypatch.setattr(settings, "SMTP_USER", email_pengirim)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", password_smtp)

    def _kirim_smtp_gagal(pesan):
        raise buat_exc(email_tujuan, email_pengirim, token_rahasia)

    monkeypatch.setattr(email_service, "_kirim_smtp", _kirim_smtp_gagal)

    with caplog.at_level(logging.ERROR):
        await email_service.kirim_email_reset_password(email_tujuan, token_rahasia)

    assert "kirim_email_reset_password_gagal" in caplog.text
    assert f"tipe={tipe_harapan}" in caplog.text
    assert f"kode={kode_harapan}" in caplog.text
    assert token_rahasia not in caplog.text
    assert "atur-ulang-password" not in caplog.text
    assert email_tujuan not in caplog.text
    assert email_pengirim not in caplog.text
    assert password_smtp not in caplog.text


async def test_kirim_email_smtp_kosong_dianggap_gagal_tanpa_mengirim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    dipanggil = []
    monkeypatch.setattr(email_service, "_kirim_smtp", lambda pesan: dipanggil.append(pesan))

    await email_service.kirim_email_reset_password("budi@contoh.com", "token-apa-saja")

    assert dipanggil == []


def test_buat_pesan_reset_tautan_tidak_dobel_garis_miring(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:5173/")

    pesan = email_service._buat_pesan_reset("budi@contoh.com", "token-apa-saja")

    isi = pesan.get_content()
    assert "http://localhost:5173/atur-ulang-password?token=token-apa-saja" in isi
    assert "5173//atur-ulang-password" not in isi
