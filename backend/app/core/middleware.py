"""Middleware batas ukuran body request.

Batas per file (10 MB) dan jumlah file per unggahan (10) sudah ada di
services/file_jawaban.py, tapi keduanya baru dicek setelah seluruh body masuk
parser multipart. Middleware ini menolak body kebesaran sedini mungkin.
"""

import logging

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import AppError

logger = logging.getLogger(__name__)

UKURAN_REQUEST_TERLALU_BESAR = AppError(
    kode="UKURAN_REQUEST_TERLALU_BESAR",
    pesan="Total ukuran file yang dikirim terlalu besar. Kurangi jumlah file lalu coba lagi.",
    status_code=413,
)


class BatasUkuranRequest:
    """Tolak request yang body-nya melebihi maks_byte.

    Dua jalur, karena Content-Length tidak selalu ada:

    1. Content-Length melebihi batas: langsung 413, body tidak pernah dibaca.
       Ini jalur yang dipakai browser, yang selalu mengisi Content-Length untuk FormData.
    2. Transfer chunked tanpa Content-Length: pesan body diserap sendiri oleh
       middleware ini (bukan lewat receive milik app) sambil dihitung, dan
       dihentikan begitu melewati batas, baru diteruskan ke app lewat receive
       pengganti yang memutar ulang pesan yang sudah diserap.

       Jalur ini sengaja TIDAK melempar exception dari dalam receive yang dibungkus
       lalu menangkapnya di sini: FastAPI membungkus pembacaan body JSON dengan
       "except Exception" generik (lihat fastapi.routing) dan mengubah exception
       apa pun yang muncul di sana menjadi HTTPException 400 "error parsing the
       body" sebelum pernah mencapai middleware ini. Dengan menyerap body di luar
       pemanggilan self.app, keputusan tolak/lanjut dibuat sebelum FastAPI mulai
       membaca sama sekali.

    Middleware ini berada DI DALAM CORSMiddleware (lihat urutan add_middleware di
    main.py) supaya respons 413 tetap membawa header CORS. Karena ia juga berada di
    luar ExceptionMiddleware, AppError di sini tidak bisa dilayani app_error_handler
    dan harus dirender sendiri menjadi JSONResponse dengan bentuk {"kode", "pesan"}
    yang sama.
    """

    def __init__(self, app: ASGIApp, maks_byte: int) -> None:
        self.app = app
        self.maks_byte = maks_byte

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self._content_length_melebihi(scope):
            await self._tolak(scope, receive, send)
            return

        if self._content_length_hadir(scope):
            # Content-Length ada dan sudah lolos pemeriksaan di atas; app boleh
            # membaca langsung lewat receive asli.
            await self.app(scope, receive, send)
            return

        pesan_tersimpan, melebihi = await self._serap_dan_hitung(receive)
        if melebihi:
            await self._tolak(scope, receive, send)
            return

        indeks = 0

        async def receive_ulang() -> Message:
            nonlocal indeks
            if indeks < len(pesan_tersimpan):
                pesan = pesan_tersimpan[indeks]
                indeks += 1
                return pesan
            return await receive()

        await self.app(scope, receive_ulang, send)

    async def _serap_dan_hitung(self, receive: Receive) -> tuple[list[Message], bool]:
        """Tarik pesan body dari receive asli sampai selesai atau melebihi batas."""
        pesan_tersimpan: list[Message] = []
        total = 0
        while True:
            message = await receive()
            pesan_tersimpan.append(message)
            if message["type"] != "http.request":
                return pesan_tersimpan, False
            total += len(message.get("body", b""))
            if total > self.maks_byte:
                return pesan_tersimpan, True
            if not message.get("more_body", False):
                return pesan_tersimpan, False

    def _content_length_hadir(self, scope: Scope) -> bool:
        return any(nama == b"content-length" for nama, _ in scope.get("headers", []))

    def _content_length_melebihi(self, scope: Scope) -> bool:
        for nama, nilai in scope.get("headers", []):
            if nama != b"content-length":
                continue
            try:
                return int(nilai) > self.maks_byte
            except ValueError:
                return False
        return False

    async def _tolak(self, scope: Scope, receive: Receive, send: Send) -> None:
        galat = UKURAN_REQUEST_TERLALU_BESAR
        logger.warning(
            "request_terlalu_besar method=%s path=%s maks_byte=%s",
            scope.get("method"),
            scope.get("path"),
            self.maks_byte,
        )
        respons = JSONResponse(
            status_code=galat.status_code,
            content={"kode": galat.kode, "pesan": galat.pesan},
        )
        await respons(scope, receive, send)
