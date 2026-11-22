import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.batch import Batch
from app.models.enums import Peran, StatusLangganan
from app.models.pengguna import Pengguna
from app.models.sesi import Sesi
from app.schemas.admin import StatusAkunFilter
from app.services.langganan import TZ_WIB, jenis_akun_efektif

AKUN_TIDAK_DITEMUKAN = AppError(
    kode="AKUN_TIDAK_DITEMUKAN",
    pesan="Akun Pengajar tidak ditemukan.",
    status_code=404,
)
MASA_BERLAKU_TIDAK_VALID = AppError(
    kode="MASA_BERLAKU_TIDAK_VALID",
    pesan="Masa berlaku wajib diisi dengan tanggal setelah hari ini.",
    status_code=400,
)
GAGAL_UBAH_LANGGANAN = AppError(
    kode="GAGAL_UBAH_LANGGANAN",
    pesan="Gagal mengubah status langganan, silakan coba lagi.",
    status_code=500,
)
GAGAL_UBAH_STATUS_AKUN = AppError(
    kode="GAGAL_UBAH_STATUS_AKUN",
    pesan="Gagal mengubah status akun, silakan coba lagi.",
    status_code=500,
)

_POLA_TANGGAL_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class AkunPengajarItem:
    id_pengguna: uuid.UUID
    nama: str
    email: str
    status_langganan: StatusLangganan
    masa_berlaku_pro: datetime | None
    dinonaktifkan_pada: datetime | None
    dibuat_pada: datetime
    jumlah_batch: int


def _escape_like(teks: str) -> str:
    return teks.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _parse_masa_berlaku_pro(nilai: Any, hari_ini_wib: date) -> datetime:
    """Validasi tanggal YYYY-MM-DD setelah hari ini (WIB) dan kembalikan
    batas akhir 23:59:59 WIB pada tanggal tersebut."""
    if isinstance(nilai, str):
        teks = nilai.strip()
        if _POLA_TANGGAL_ISO.match(teks) is None:
            raise MASA_BERLAKU_TIDAK_VALID
        try:
            tanggal = date.fromisoformat(teks)
        except ValueError:
            raise MASA_BERLAKU_TIDAK_VALID from None
    elif type(nilai) is date:
        tanggal = nilai
    else:
        raise MASA_BERLAKU_TIDAK_VALID

    if tanggal <= hari_ini_wib:
        raise MASA_BERLAKU_TIDAK_VALID

    return datetime(tanggal.year, tanggal.month, tanggal.day, 23, 59, 59, tzinfo=TZ_WIB)


def _ke_item(pengguna: Pengguna, jumlah_batch: int, sekarang: datetime) -> AkunPengajarItem:
    efektif = jenis_akun_efektif(pengguna, sekarang)
    return AkunPengajarItem(
        id_pengguna=pengguna.id_pengguna,
        nama=pengguna.nama,
        email=pengguna.email,
        status_langganan=efektif,
        masa_berlaku_pro=pengguna.masa_berlaku_pro if efektif == StatusLangganan.PRO else None,
        dinonaktifkan_pada=pengguna.dinonaktifkan_pada,
        dibuat_pada=pengguna.dibuat_pada,
        jumlah_batch=jumlah_batch,
    )


async def _ambil_pengajar_untuk_update(db: AsyncSession, id_pengguna: uuid.UUID) -> Pengguna:
    pengguna = await db.scalar(
        select(Pengguna)
        .where(Pengguna.id_pengguna == id_pengguna, Pengguna.peran == Peran.PENGAJAR)
        .with_for_update()
    )
    if pengguna is None:
        raise AKUN_TIDAK_DITEMUKAN
    return pengguna


async def _hitung_jumlah_batch(db: AsyncSession, id_pengguna: uuid.UUID) -> int:
    jumlah = await db.scalar(
        select(func.count()).select_from(Batch).where(Batch.id_pengguna == id_pengguna)
    )
    return int(jumlah or 0)


async def daftar_akun_pengajar(
    db: AsyncSession,
    *,
    cari: str | None = None,
    status_langganan: StatusLangganan | None = None,
    status_akun: StatusAkunFilter | None = None,
) -> list[AkunPengajarItem]:
    """Ambil daftar akun Pengajar (Admin tidak ikut) dengan pencarian dan filter."""
    sekarang = datetime.now(UTC)

    jumlah_batch_subq = (
        select(
            Batch.id_pengguna,
            func.count(Batch.id_batch).label("jumlah_batch"),
        )
        .group_by(Batch.id_pengguna)
        .subquery()
    )

    stmt = (
        select(
            Pengguna,
            func.coalesce(jumlah_batch_subq.c.jumlah_batch, 0).label("jumlah_batch"),
        )
        .outerjoin(jumlah_batch_subq, Pengguna.id_pengguna == jumlah_batch_subq.c.id_pengguna)
        .where(Pengguna.peran == Peran.PENGAJAR)
    )

    if cari is not None:
        kata_kunci = cari.strip()
        if kata_kunci:
            pola = f"%{_escape_like(kata_kunci)}%"
            stmt = stmt.where(
                or_(
                    Pengguna.nama.ilike(pola, escape="\\"),
                    Pengguna.email.ilike(pola, escape="\\"),
                )
            )

    if status_langganan is StatusLangganan.PRO:
        stmt = stmt.where(
            Pengguna.status_langganan == StatusLangganan.PRO,
            or_(Pengguna.masa_berlaku_pro.is_(None), Pengguna.masa_berlaku_pro > sekarang),
        )
    elif status_langganan is StatusLangganan.FREE:
        stmt = stmt.where(
            or_(
                Pengguna.status_langganan != StatusLangganan.PRO,
                and_(
                    Pengguna.masa_berlaku_pro.is_not(None),
                    Pengguna.masa_berlaku_pro <= sekarang,
                ),
            )
        )

    if status_akun is StatusAkunFilter.AKTIF:
        stmt = stmt.where(Pengguna.dinonaktifkan_pada.is_(None))
    elif status_akun is StatusAkunFilter.NONAKTIF:
        stmt = stmt.where(Pengguna.dinonaktifkan_pada.is_not(None))

    stmt = stmt.order_by(Pengguna.dibuat_pada.desc(), Pengguna.id_pengguna.desc())
    rows = (await db.execute(stmt)).all()
    return [_ke_item(pengguna, int(jumlah_batch), sekarang) for pengguna, jumlah_batch in rows]


async def ubah_langganan_pengajar(
    db: AsyncSession,
    id_pengguna: uuid.UUID,
    status_langganan: StatusLangganan,
    masa_berlaku_pro: Any = None,
) -> AkunPengajarItem:
    """Ubah status langganan Pengajar (Free mengosongkan masa berlaku, Pro berlaku
    inklusif sampai 23:59:59 WIB pada tanggal masa berlaku)."""
    batas_pro: datetime | None = None
    if status_langganan is StatusLangganan.PRO:
        batas_pro = _parse_masa_berlaku_pro(masa_berlaku_pro, datetime.now(TZ_WIB).date())

    pengguna = await _ambil_pengajar_untuk_update(db, id_pengguna)
    pengguna.status_langganan = status_langganan
    pengguna.masa_berlaku_pro = batas_pro

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_UBAH_LANGGANAN from None

    jumlah_batch = await _hitung_jumlah_batch(db, pengguna.id_pengguna)
    return _ke_item(pengguna, jumlah_batch, datetime.now(UTC))


async def nonaktifkan_pengajar(db: AsyncSession, id_pengguna: uuid.UUID) -> AkunPengajarItem:
    """Nonaktifkan akun Pengajar dan cabut seluruh sesi aktifnya dalam satu transaksi.
    Data akun dan batch tetap tersimpan."""
    pengguna = await _ambil_pengajar_untuk_update(db, id_pengguna)
    sekarang = datetime.now(UTC)

    if pengguna.dinonaktifkan_pada is None:
        pengguna.dinonaktifkan_pada = sekarang

    await db.execute(
        update(Sesi)
        .where(Sesi.id_pengguna == pengguna.id_pengguna, Sesi.dicabut_pada.is_(None))
        .values(dicabut_pada=sekarang)
    )
    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_UBAH_STATUS_AKUN from None

    jumlah_batch = await _hitung_jumlah_batch(db, pengguna.id_pengguna)
    return _ke_item(pengguna, jumlah_batch, sekarang)


async def aktifkan_pengajar(db: AsyncSession, id_pengguna: uuid.UUID) -> AkunPengajarItem:
    """Aktifkan kembali akun Pengajar agar dapat masuk kembali."""
    pengguna = await _ambil_pengajar_untuk_update(db, id_pengguna)
    pengguna.dinonaktifkan_pada = None

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise GAGAL_UBAH_STATUS_AKUN from None

    jumlah_batch = await _hitung_jumlah_batch(db, pengguna.id_pengguna)
    return _ke_item(pengguna, jumlah_batch, datetime.now(UTC))
