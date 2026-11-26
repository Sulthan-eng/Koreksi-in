// Fungsi murni (tanpa import.meta/DOM) agar bisa diuji oleh node --test.
import { dapatkanPaketPro, formatRupiah } from "./langganan.js";

const LABEL_STATUS_TRANSAKSI = {
  menunggu: "Menunggu",
  berhasil: "Berhasil",
  gagal: "Gagal",
  kedaluwarsa: "Kedaluwarsa",
};

const ZONA_WIB = "Asia/Jakarta";

function formatWaktuWib(iso) {
  if (typeof iso !== "string" || !iso) return "";
  const tanggal = new Date(iso);
  if (Number.isNaN(tanggal.getTime())) return "";
  const terformat = new Intl.DateTimeFormat("id-ID", {
    timeZone: ZONA_WIB,
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(tanggal);
  return `${terformat} WIB`;
}

export function buatPesanKendalaPembayaran({ nama, email, transaksi } = {}) {
  const baris = ["Halo Admin Koreksi-in, saya mengalami kendala pembayaran."];

  if (typeof nama === "string" && nama.trim()) {
    baris.push(`Nama: ${nama}`);
  }
  if (typeof email === "string" && email.trim()) {
    baris.push(`Email akun: ${email}`);
  }

  if (transaksi && typeof transaksi === "object") {
    if (typeof transaksi.paket === "string") {
      const paket = dapatkanPaketPro(transaksi.paket);
      if (paket) {
        baris.push(`Paket: ${paket.ringkasanTeks}`);
      }
    }
    if (typeof transaksi.nominal === "number") {
      baris.push(`Nominal: ${formatRupiah(transaksi.nominal)}`);
    }
    const labelStatus = LABEL_STATUS_TRANSAKSI[transaksi.status];
    if (labelStatus) {
      baris.push(`Status: ${labelStatus}`);
    }
    const waktu = formatWaktuWib(transaksi.dibuat_pada);
    if (waktu) {
      baris.push(`Waktu transaksi: ${waktu}`);
    }
    if (typeof transaksi.id_order === "string" && transaksi.id_order) {
      baris.push(`Order ID: ${transaksi.id_order}`);
    }
  }

  return baris.join("\n");
}

export function buatTautanWhatsAppAdmin({ nomor, pesan } = {}) {
  const nomorBersih =
    typeof nomor === "string" ? nomor.replace(/[\s+-]/g, "") : "";
  if (!nomorBersih) return null;
  return `https://wa.me/${nomorBersih}?text=${encodeURIComponent(pesan ?? "")}`;
}
