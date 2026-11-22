import io
import logging
import re
import sys

from app import main as app_main
from app.core.logging import _NAMA_HANDLER_STDOUT, _NAMA_LOGGER_APP, atur_logging

_POLA_ISO_OFFSET = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4} ")


def test_atur_logging_konfigurasi_stdout_level_info_dan_format(monkeypatch) -> None:
    app_logger = logging.getLogger(_NAMA_LOGGER_APP)
    handlers_lama = list(app_logger.handlers)
    level_lama = app_logger.level
    propagate_lama = app_logger.propagate

    buffer = io.StringIO()
    try:
        app_logger.handlers.clear()
        app_logger.setLevel(logging.NOTSET)
        monkeypatch.setattr(sys, "stdout", buffer)

        hasil = atur_logging()

        assert hasil is app_logger
        assert app_logger.level == logging.INFO
        assert app_logger.propagate is True

        handler_app = [
            h for h in app_logger.handlers if getattr(h, "name", None) == _NAMA_HANDLER_STDOUT
        ]
        assert len(handler_app) == 1
        assert isinstance(handler_app[0], logging.StreamHandler)
        assert handler_app[0].stream is buffer

        logging.getLogger("app.services.gemini").info(
            "gemini_call model=%s items=%d daily_count=%d attempt=%d",
            "gemini-3.5-flash-lite",
            3,
            1,
            1,
        )
    finally:
        app_logger.handlers[:] = handlers_lama
        app_logger.setLevel(level_lama)
        app_logger.propagate = propagate_lama

    baris = buffer.getvalue().strip()
    assert _POLA_ISO_OFFSET.match(baris), f"Format waktu tidak sesuai ISO+offset: {baris!r}"
    assert " INFO app.services.gemini gemini_call " in baris
    assert "model=gemini-3.5-flash-lite items=3 daily_count=1 attempt=1" in baris


def test_atur_logging_idempoten_tidak_duplikasi_handler() -> None:
    app_logger = logging.getLogger(_NAMA_LOGGER_APP)
    atur_logging()
    atur_logging()
    app_main.buat_app()

    handler_app = [
        h for h in app_logger.handlers if getattr(h, "name", None) == _NAMA_HANDLER_STDOUT
    ]
    assert len(handler_app) == 1


def test_atur_logging_tetap_kompatibel_dengan_caplog(caplog) -> None:
    atur_logging()
    with caplog.at_level(logging.INFO):
        logging.getLogger("app.services.gemini").info("uji_caplog_info count=%d", 7)

    assert "uji_caplog_info count=7" in caplog.text


def test_atur_logging_tidak_menyentuh_root_atau_logger_pihak_ketiga() -> None:
    root = logging.getLogger()
    level_root_sebelum = root.level
    handler_root_sebelum = list(root.handlers)

    atur_logging()

    assert root.level == level_root_sebelum
    assert not any(getattr(h, "name", None) == _NAMA_HANDLER_STDOUT for h in root.handlers)
    assert list(root.handlers) == handler_root_sebelum

    for nama_pihak_ketiga in ("httpx", "botocore", "google_genai"):
        logger_luar = logging.getLogger(nama_pihak_ketiga)
        assert not any(
            getattr(h, "name", None) == _NAMA_HANDLER_STDOUT for h in logger_luar.handlers
        )


def test_main_memakai_logger_app_main() -> None:
    assert app_main.logger.name == "app.main"
