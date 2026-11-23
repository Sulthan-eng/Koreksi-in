import enum


class StatusLangganan(enum.Enum):
    FREE = "free"
    PRO = "pro"


class StatusBatch(enum.Enum):
    AKTIF = "aktif"
    SELESAI = "selesai"


class StatusProses(enum.Enum):
    DIPROSES = "diproses"
    SELESAI = "selesai"
    GAGAL = "gagal"


class Kategori(enum.Enum):
    SANGAT_MIRIP = "sangat_mirip"
    CUKUP_MIRIP = "cukup_mirip"
    KURANG_MIRIP = "kurang_mirip"


class Peran(enum.Enum):
    PENGAJAR = "pengajar"
    ADMIN = "admin"


class PaketLangganan(enum.Enum):
    PRO_1_BULAN = "pro_1_bulan"
    PRO_3_BULAN = "pro_3_bulan"


class StatusTransaksi(enum.Enum):
    MENUNGGU = "menunggu"
    BERHASIL = "berhasil"
    GAGAL = "gagal"
    KEDALUWARSA = "kedaluwarsa"


def nilai_enum(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]
