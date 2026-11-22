"""Konfigurasi logging aplikasi (logger `app.*`) ke stdout.

Uvicorn secara default hanya mengonfigurasi logger `uvicorn`, `uvicorn.access`,
dan `uvicorn.error`; logger `app.*` tidak punya handler sehingga log level INFO
(mis. hitungan panggilan Gemini) tidak tampil di `fly logs`. Modul ini
mengonfigurasi logger `app` saja memakai stdlib, tanpa menyentuh root logger
maupun logger pustaka pihak ketiga.
"""

import logging
import sys

_NAMA_LOGGER_APP = "app"
_NAMA_HANDLER_STDOUT = "koreksi_in_stdout"
_FORMAT_LOG = "%(asctime)s %(levelname)s %(name)s %(message)s"
_FORMAT_WAKTU = "%Y-%m-%dT%H:%M:%S%z"


def atur_logging() -> logging.Logger:
    """Siapkan handler stdout berformat rapi pada logger `app` di level INFO.

    Idempoten agar aman dipanggil berulang oleh factory `buat_app()`.
    `propagate` dibiarkan True supaya `caplog` pytest (yang menempel di root
    logger) tetap menangkap log; di runtime uvicorn root tidak punya handler
    sehingga setiap baris tetap tercetak tepat sekali di stdout.
    """
    app_logger = logging.getLogger(_NAMA_LOGGER_APP)
    app_logger.setLevel(logging.INFO)

    if not any(getattr(h, "name", None) == _NAMA_HANDLER_STDOUT for h in app_logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.name = _NAMA_HANDLER_STDOUT
        handler.setFormatter(logging.Formatter(fmt=_FORMAT_LOG, datefmt=_FORMAT_WAKTU))
        app_logger.addHandler(handler)

    return app_logger
