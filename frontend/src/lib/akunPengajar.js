const ZONA_WIB = "Asia/Jakarta";
const POLA_TANGGAL_ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

function bagianTanggalWib(tanggal) {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_WIB,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const peta = {};
  for (const bagian of formatter.formatToParts(tanggal)) {
    if (
      bagian.type === "year" ||
      bagian.type === "month" ||
      bagian.type === "day"
    ) {
      peta[bagian.type] = bagian.value;
    }
  }
  return `${peta.year}-${peta.month}-${peta.day}`;
}

export function formatTanggalWib(iso) {
  if (!iso) return "";
  return new Intl.DateTimeFormat("id-ID", {
    timeZone: ZONA_WIB,
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso));
}

export function keTanggalInputWib(iso) {
  if (!iso) return "";
  const tanggal = new Date(iso);
  if (Number.isNaN(tanggal.getTime())) return "";
  return bagianTanggalWib(tanggal);
}

export function hariIniWib(sekarang = new Date()) {
  return bagianTanggalWib(sekarang);
}

export function validasiMasaBerlakuPro(nilaiTanggal, sekarang = new Date()) {
  if (typeof nilaiTanggal !== "string") return false;
  const teks = nilaiTanggal.trim();
  const cocok = POLA_TANGGAL_ISO.exec(teks);
  if (!cocok) return false;

  const tahun = Number(cocok[1]);
  const bulan = Number(cocok[2]);
  const hari = Number(cocok[3]);
  const uji = new Date(Date.UTC(tahun, bulan - 1, hari));
  if (
    uji.getUTCFullYear() !== tahun ||
    uji.getUTCMonth() !== bulan - 1 ||
    uji.getUTCDate() !== hari
  ) {
    return false;
  }

  return teks > hariIniWib(sekarang);
}

export function apakahCocokFilterAkun(
  akun,
  { statusLangganan = "", statusAkun = "" } = {},
) {
  if (statusLangganan !== "" && akun.status_langganan !== statusLangganan) {
    return false;
  }
  const statusSekarang = akun.dinonaktifkan_pada ? "nonaktif" : "aktif";
  if (statusAkun !== "" && statusSekarang !== statusAkun) {
    return false;
  }
  return true;
}

export function terapkanPerubahanAkun(daftar, akunBaru, filter = {}) {
  const cocok = apakahCocokFilterAkun(akunBaru, filter);
  if (!cocok) {
    return daftar.filter((item) => item.id_pengguna !== akunBaru.id_pengguna);
  }
  return daftar.map((item) =>
    item.id_pengguna === akunBaru.id_pengguna ? akunBaru : item,
  );
}

export function apakahGalatJaringan(
  error,
  online = typeof navigator !== "undefined" ? navigator.onLine : true,
) {
  return Boolean(error?.jaringan) || online === false;
}
