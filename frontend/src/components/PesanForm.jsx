const VARIAN_PESAN = {
  sukses: {
    role: "status",
    warna: "text-sangat-mirip",
  },
  galat: {
    role: "alert",
    warna: "text-kurang-mirip",
  },
};

function PesanForm({ varian = "galat", pesan, className = "" }) {
  if (!pesan) return null;

  const konfigurasi = VARIAN_PESAN[varian] ?? VARIAN_PESAN.galat;

  return (
    <p
      role={konfigurasi.role}
      className={`${konfigurasi.warna} ${className}`.trim()}
    >
      {pesan}
    </p>
  );
}

export default PesanForm;
