import Spinner from "./Spinner.jsx";

const KELAS_DASAR =
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-semibold leading-5 whitespace-nowrap";

const VARIAN_LENCANA = {
  // Status pemrosesan
  diproses: {
    teks: "Diproses",
    kelas: "bg-biru-muda text-biru-utama",
    pakaiSpinner: true,
  },
  selesai: {
    teks: "Selesai",
    kelas: "bg-sangat-mirip-latar text-sangat-mirip",
  },
  gagal: {
    teks: "Gagal",
    kelas: "bg-kurang-mirip-latar text-kurang-mirip",
  },

  // Kategori kualitatif
  sangat_mirip: {
    teks: "Sangat Mirip",
    kelas: "bg-sangat-mirip-latar text-sangat-mirip",
  },
  cukup_mirip: {
    teks: "Cukup Mirip",
    kelas: "bg-cukup-mirip-latar text-cukup-mirip",
  },
  kurang_mirip: {
    teks: "Kurang Mirip",
    kelas: "bg-kurang-mirip-latar text-kurang-mirip",
  },

  // Status langganan
  free: {
    teks: "FREE",
    kelas: "border border-garis bg-latar text-teks-redup",
  },
  pro: {
    teks: "PRO",
    kelas: "bg-biru-utama text-permukaan",
  },

  // Status akun & batch
  aktif: {
    teks: "Aktif",
    kelas: "bg-sangat-mirip-latar text-sangat-mirip",
  },
  nonaktif: {
    teks: "Nonaktif",
    kelas: "border border-garis bg-latar text-teks-redup",
  },
  batch_aktif: {
    teks: "Aktif",
    kelas: "bg-biru-muda text-biru-utama",
  },
  batch_selesai: {
    teks: "Selesai",
    kelas: "border border-garis bg-latar text-teks-redup",
  },

  // Status transaksi
  menunggu: {
    teks: "Menunggu",
    kelas: "bg-biru-muda text-biru-utama",
  },
  berhasil: {
    teks: "Berhasil",
    kelas: "bg-sangat-mirip-latar text-sangat-mirip",
  },
  kedaluwarsa: {
    teks: "Kedaluwarsa",
    kelas: "border border-garis bg-latar text-teks-redup",
  },
};

export function Lencana({ varian }) {
  const konfigurasi = VARIAN_LENCANA[varian];
  if (!konfigurasi) return null;

  return (
    <span className={`${KELAS_DASAR} ${konfigurasi.kelas}`}>
      {konfigurasi.pakaiSpinner && <Spinner ukuran="size-3.5" />}
      {konfigurasi.teks}
    </span>
  );
}

export default Lencana;
