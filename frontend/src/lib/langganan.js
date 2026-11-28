import { BATAS_GAGAL_POLLING, catatHasilPolling } from "./pollingStatus.js";

export const JEDA_POLLING_TRANSAKSI_MS = 3000;
export const MAKS_PERCOBAAN_POLLING_TRANSAKSI = 10;

export const DAFTAR_PAKET_PRO = [
  {
    kode: "pro_1_bulan",
    namaPaket: "Langganan Pro 1 Bulan",
    labelDurasi: "1 bulan (30 hari)",
    durasiHari: 30,
    nominal: 30000,
    hargaTeks: "Rp 30.000",
    ringkasanTeks: "1 bulan (30 hari), Rp 30.000",
  },
  {
    kode: "pro_3_bulan",
    namaPaket: "Langganan Pro 3 Bulan",
    labelDurasi: "3 bulan (90 hari)",
    durasiHari: 90,
    nominal: 80000,
    hargaTeks: "Rp 80.000",
    ringkasanTeks: "3 bulan (90 hari), Rp 80.000",
  },
];

const ZONA_WIB = "Asia/Jakarta";

const NAMA_BULAN_PANJANG = [
  "Januari",
  "Februari",
  "Maret",
  "April",
  "Mei",
  "Juni",
  "Juli",
  "Agustus",
  "September",
  "Oktober",
  "November",
  "Desember",
];

const NAMA_BULAN_SINGKAT = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "Mei",
  "Jun",
  "Jul",
  "Agu",
  "Sep",
  "Okt",
  "Nov",
  "Des",
];

function ekstrakBagianWaktuWib(iso) {
  if (!iso) return null;
  const tanggal = new Date(iso);
  if (Number.isNaN(tanggal.getTime())) return null;
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_WIB,
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  const peta = {};
  for (const bagian of formatter.formatToParts(tanggal)) {
    if (
      bagian.type === "year" ||
      bagian.type === "month" ||
      bagian.type === "day" ||
      bagian.type === "hour" ||
      bagian.type === "minute"
    ) {
      peta[bagian.type] = bagian.value;
    }
  }
  return {
    hari: Number(peta.day),
    indeksBulan: Number(peta.month) - 1,
    tahun: peta.year,
    jam: peta.hour,
    menit: peta.minute,
  };
}

const PETA_PAKET_PRO = new Map(
  DAFTAR_PAKET_PRO.map((item) => [item.kode, item]),
);

export const DAFTAR_MANFAAT_PRO = [
  "Batch aktif tidak dibatasi",
  "30 soal per batch",
  "50 jawaban per batch",
  "Ekspor rekap nilai",
];

const FRASA_TAUTAN_PER_KODE = {
  BATAS_BATCH_AKTIF_TERCAPAI: "Upgrade ke Pro",
  BATAS_JAWABAN_TERLAMPAUI: "upgrade ke Pro",
  EKSPOR_KHUSUS_PRO: "Upgrade",
};

export function dapatkanPaketPro(kodePaket) {
  return PETA_PAKET_PRO.get(kodePaket) ?? DAFTAR_PAKET_PRO[0];
}

export function formatRupiah(nominal) {
  const angka = Number(nominal);
  if (!Number.isFinite(angka)) return "Rp 0";
  return `Rp ${Math.trunc(angka).toLocaleString("id-ID")}`;
}

export function formatRingkasanPaket(kodePaket) {
  return dapatkanPaketPro(kodePaket).ringkasanTeks;
}

export function namaPaketTransaksi(kodePaket) {
  return dapatkanPaketPro(kodePaket).namaPaket;
}

export function formatTanggalSingkatWib(iso) {
  const bagian = ekstrakBagianWaktuWib(iso);
  if (!bagian) return "";
  return `${bagian.hari} ${NAMA_BULAN_SINGKAT[bagian.indeksBulan]} ${bagian.tahun}`;
}

export function formatTanggalJamWib(iso) {
  const bagian = ekstrakBagianWaktuWib(iso);
  if (!bagian) return "";
  return `${bagian.hari} ${NAMA_BULAN_PANJANG[bagian.indeksBulan]} ${bagian.tahun}, ${bagian.jam}.${bagian.menit} WIB`;
}

export function formatMetodePembayaran(metode) {
  if (typeof metode !== "string") return "-";
  const bersih = metode.trim();
  return bersih || "-";
}

export function formatRingkasanTransaksi(transaksi) {
  if (!transaksi || typeof transaksi !== "object") {
    return DAFTAR_PAKET_PRO[0].ringkasanTeks;
  }
  const paket = dapatkanPaketPro(transaksi.paket);
  const harga =
    typeof transaksi.nominal === "number" && transaksi.nominal !== paket.nominal
      ? formatRupiah(transaksi.nominal)
      : paket.hargaTeks;
  return `${paket.labelDurasi}, ${harga}`;
}

export function labelTombolLangganan(statusLangganan) {
  return statusLangganan === "pro" ? "Perpanjang Pro" : "Upgrade ke Pro";
}

export function ambilTransaksiTerakhir(daftarTransaksi) {
  if (!Array.isArray(daftarTransaksi) || daftarTransaksi.length === 0) {
    return null;
  }
  return daftarTransaksi[0] ?? null;
}

export function langkahPollingTransaksi({
  statusTransaksi,
  percobaanSaatIni,
  gagalBeruntunSaatIni,
  berhasil,
  maksPercobaan = MAKS_PERCOBAAN_POLLING_TRANSAKSI,
  batasGagal = BATAS_GAGAL_POLLING,
}) {
  const percobaan = percobaanSaatIni + 1;

  if (!berhasil) {
    const hasilGagal = catatHasilPolling(
      gagalBeruntunSaatIni,
      false,
      batasGagal,
    );
    const berhenti = hasilGagal.berhenti || percobaan >= maksPercobaan;
    return {
      percobaan,
      gagalBeruntun: hasilGagal.gagalBeruntun,
      berhenti,
      belumTerkonfirmasi: berhenti,
      perluMuatUlangProfil: false,
    };
  }

  if (statusTransaksi !== "menunggu") {
    return {
      percobaan,
      gagalBeruntun: 0,
      berhenti: true,
      belumTerkonfirmasi: false,
      perluMuatUlangProfil: statusTransaksi === "berhasil",
    };
  }

  const berhenti = percobaan >= maksPercobaan;
  return {
    percobaan,
    gagalBeruntun: 0,
    berhenti,
    belumTerkonfirmasi: berhenti,
    perluMuatUlangProfil: false,
  };
}

/**
 * Pecah pesan penolakan kuota/fitur akun Free menjadi { awalan, teksTautan, akhiran }
 * berdasarkan kode error (BATAS_BATCH_AKTIF_TERCAPAI, BATAS_JAWABAN_TERLAMPAUI
 * khusus Free, dan EKSPOR_KHUSUS_PRO). Kembalikan null untuk kode lain atau
 * pesan BATAS_JAWABAN_TERLAMPAUI milik akun Pro.
 */
export function pecahPesanPenolakanLangganan(kode, pesan) {
  if (typeof kode !== "string" || typeof pesan !== "string") {
    return null;
  }
  const frasa = FRASA_TAUTAN_PER_KODE[kode];
  if (!frasa) {
    return null;
  }
  const indeks = pesan.indexOf(frasa);
  if (indeks === -1) {
    return null;
  }
  return {
    awalan: pesan.slice(0, indeks),
    teksTautan: frasa,
    akhiran: pesan.slice(indeks + frasa.length),
  };
}
