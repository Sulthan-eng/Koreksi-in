const FORMAT_ANGKA = new Intl.NumberFormat("id-ID");

export function formatAngka(nilai) {
  const angka = Number(nilai);
  if (!Number.isFinite(angka)) {
    return "0";
  }
  return FORMAT_ANGKA.format(Math.trunc(angka));
}

export function formatPersenPemakaian(terpakai, batas) {
  const pakai = Number(terpakai);
  const maks = Number(batas);
  if (
    !Number.isFinite(pakai) ||
    !Number.isFinite(maks) ||
    maks <= 0 ||
    pakai <= 0
  ) {
    return "0%";
  }
  if (pakai >= maks) {
    return "100%";
  }

  const persepuluh = Math.floor((pakai * 1000) / maks);
  const utuh = Math.floor(persepuluh / 10);
  const desimal = persepuluh % 10;
  return desimal === 0 ? `${utuh}%` : `${utuh},${desimal}%`;
}

export function lebarBilahKuota(terpakai, batas) {
  const pakai = Number(terpakai);
  const maks = Number(batas);
  if (
    !Number.isFinite(pakai) ||
    !Number.isFinite(maks) ||
    maks <= 0 ||
    pakai <= 0
  ) {
    return "0%";
  }
  if (pakai >= maks) {
    return "100%";
  }
  return `${(pakai / maks) * 100}%`;
}

export function sisaPanggilan(terpakai, batas) {
  const pakai = Number(terpakai);
  const maks = Number(batas);
  if (!Number.isFinite(pakai) || !Number.isFinite(maks)) {
    return 0;
  }
  return Math.max(0, maks - pakai);
}

export function tingkatKuota(terpakai, batas) {
  const pakai = Number(terpakai);
  const maks = Number(batas);
  if (
    !Number.isFinite(pakai) ||
    !Number.isFinite(maks) ||
    maks <= 0 ||
    pakai >= maks
  ) {
    return "batas-tercapai";
  }
  if (pakai * 100 >= maks * 95) {
    return "hampir-habis";
  }
  if (pakai * 100 >= maks * 80) {
    return "mendekati-batas";
  }
  return "normal";
}

export function labelTingkatKuota(tingkat) {
  switch (tingkat) {
    case "mendekati-batas":
      return "Mendekati batas";
    case "hampir-habis":
      return "Hampir habis";
    case "batas-tercapai":
      return "Batas tercapai";
    default:
      return null;
  }
}

export function formatJamDiperbarui(tanggal) {
  if (!(tanggal instanceof Date) || Number.isNaN(tanggal.getTime())) {
    return "";
  }
  const jam = String(tanggal.getHours()).padStart(2, "0");
  const menit = String(tanggal.getMinutes()).padStart(2, "0");
  return `${jam}.${menit}`;
}
