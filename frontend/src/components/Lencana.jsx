import Spinner from "./Spinner.jsx";

const KELAS_STATUS_PROSES = {
  diproses: "bg-biru-muda text-biru-utama",
  selesai: "bg-sangat-mirip-latar text-sangat-mirip",
  gagal: "bg-kurang-mirip-latar text-kurang-mirip",
};

const TEKS_STATUS_PROSES = {
  diproses: "Diproses",
  selesai: "Selesai",
  gagal: "Gagal",
};

export function LencanaStatusProses({ statusProses }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ${KELAS_STATUS_PROSES[statusProses]}`}
    >
      {statusProses === "diproses" && <Spinner className="h-3 w-3 text-biru-utama" />}
      {TEKS_STATUS_PROSES[statusProses]}
    </span>
  );
}

const KELAS_KATEGORI = {
  sangat_mirip: "bg-sangat-mirip-latar text-sangat-mirip",
  cukup_mirip: "bg-cukup-mirip-latar text-cukup-mirip",
  kurang_mirip: "bg-kurang-mirip-latar text-kurang-mirip",
};

const TEKS_KATEGORI = {
  sangat_mirip: "Sangat Mirip",
  cukup_mirip: "Cukup Mirip",
  kurang_mirip: "Kurang Mirip",
};

export function LencanaKategori({ kategori }) {
  if (!kategori) return null;
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm ${KELAS_KATEGORI[kategori]}`}
    >
      {TEKS_KATEGORI[kategori]}
    </span>
  );
}
