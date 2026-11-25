const DURASI_JEDA_DETIK = 60;

export const KUNCI_SESSION_STORAGE_LUPA_PASSWORD =
  "lupaPassword.statusTerkirim";

export function sisaDetik(waktuBerakhir, sekarang) {
  const detik = Math.ceil((waktuBerakhir - sekarang) / 1000);
  return Math.min(DURASI_JEDA_DETIK, Math.max(0, detik));
}

export function waktuBerakhirBaru(sekarang) {
  return sekarang + DURASI_JEDA_DETIK * 1000;
}

export function bacaStatusTersimpan(nilaiMentah, sekarang) {
  if (typeof nilaiMentah !== "string" || nilaiMentah === "") {
    return null;
  }

  let data;
  try {
    data = JSON.parse(nilaiMentah);
  } catch {
    return null;
  }

  if (
    data === null ||
    typeof data !== "object" ||
    typeof data.email !== "string" ||
    data.email === "" ||
    typeof data.waktuBerakhir !== "number" ||
    !Number.isFinite(data.waktuBerakhir)
  ) {
    return null;
  }

  const sisa = sisaDetik(data.waktuBerakhir, sekarang);
  if (sisa <= 0) {
    return null;
  }

  return {
    email: data.email,
    sisaDetik: sisa,
    waktuBerakhir: data.waktuBerakhir,
  };
}

export function labelTombolLupaPassword(sisaDetikTersisa) {
  return sisaDetikTersisa > 0
    ? `Kirim ulang dalam ${sisaDetikTersisa} detik`
    : "Kirim Tautan";
}
