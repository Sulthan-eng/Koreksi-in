import importlib

import sqlalchemy.ext.asyncio as sa_asyncio

import app.core.database as database_module


def test_engine_dibuat_dengan_pengaturan_pool(monkeypatch):
    """Cek kwargs yang dikirim ke create_async_engine, bukan atribut privat
    SQLAlchemy Pool (_pre_ping, _recycle, dst.) yang bukan API publik dan bisa
    berubah antar versi. database.py membuat engine saat modul diimpor, jadi
    perlu di-reload agar stub ini terpakai; patch dipasang di modul sumber
    (sqlalchemy.ext.asyncio), bukan di database_module, karena reload
    menjalankan ulang baris `from ... import create_async_engine` yang akan
    menimpa patch kalau dipasang di database_module. Modul dikembalikan ke
    kondisi asli di finally (undo monkeypatch lalu reload ulang dengan
    create_async_engine asli) supaya test lain tidak memakai engine dummy.
    """
    rekaman = {}

    def _stub_create_async_engine(url, **kwargs):
        rekaman["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(sa_asyncio, "create_async_engine", _stub_create_async_engine)
    importlib.reload(database_module)
    try:
        assert rekaman["kwargs"] == {
            "pool_pre_ping": True,
            "pool_recycle": database_module.settings.DB_POOL_RECYCLE_SECONDS,
            "pool_size": database_module.settings.DB_POOL_SIZE,
            "max_overflow": database_module.settings.DB_MAX_OVERFLOW,
        }
    finally:
        monkeypatch.undo()
        importlib.reload(database_module)
