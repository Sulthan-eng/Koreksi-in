import logging

import pytest

from app.core.config import settings
from app.services import email as email_service


async def test_kirim_email_reset_token_tidak_pernah_dicatat_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(settings, "SMTP_USER", "pengirim@contoh.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "rahasia-app-password")

    def _kirim_smtp_gagal(pesan):
        raise OSError("gagal konek SMTP")

    monkeypatch.setattr(email_service, "_kirim_smtp", _kirim_smtp_gagal)

    token_rahasia = "token-rahasia-tidak-boleh-bocor"
    with caplog.at_level(logging.ERROR):
        await email_service.kirim_email_reset_password("budi@contoh.com", token_rahasia)

    assert token_rahasia not in caplog.text


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
