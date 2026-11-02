const VARIAN_PESAN = {
  sukses: {
    role: "status",
    warna: "text-sangat-mirip",
    latar: "bg-sangat-mirip-latar",
  },
  galat: {
    role: "alert",
    warna: "text-kurang-mirip",
    latar: "bg-kurang-mirip-latar",
  },
  netral: {
    warna: "text-teks",
    latar: "bg-biru-muda",
  },
};

function PesanForm({
  varian = "galat",
  pesan,
  id,
  className = "",
  kotak = false,
}) {
  if (!pesan) return null;

  const konfigurasi = VARIAN_PESAN[varian] ?? VARIAN_PESAN.galat;

  const kotakClass = kotak
    ? `rounded-lg px-4 py-3 text-sm leading-5 ${konfigurasi.latar}`
    : "";

  return (
    <p
      id={id}
      role={konfigurasi.role}
      className={`${konfigurasi.warna} ${kotakClass} ${className}`.trim()}
    >
      {pesan}
    </p>
  );
}

export default PesanForm;
