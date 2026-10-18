import uuid

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import StatusProses
from app.models.file_jawaban import FileJawaban
from app.models.hasil_koreksi import HasilKoreksi
from app.models.pengguna import Pengguna
from app.models.soal import Soal
from app.services.batch import ambil_batch


async def daftar_hasil_koreksi(
    db: AsyncSession, pengguna: Pengguna, id_batch: uuid.UUID
) -> list[Row]:
    batch = await ambil_batch(db, pengguna, id_batch)
    hasil = await db.execute(
        select(
            FileJawaban.id_file,
            FileJawaban.nama_peserta_didik,
            Soal.no_soal,
            HasilKoreksi.teks_ocr,
            HasilKoreksi.skor_sistem,
            HasilKoreksi.kategori,
        )
        .join(HasilKoreksi, HasilKoreksi.id_file == FileJawaban.id_file)
        .join(Soal, Soal.id_soal == HasilKoreksi.id_soal)
        .where(
            FileJawaban.id_batch == batch.id_batch,
            FileJawaban.status_proses == StatusProses.SELESAI,
        )
        .order_by(FileJawaban.diunggah_pada.asc(), Soal.no_soal.asc())
    )
    return list(hasil.all())
