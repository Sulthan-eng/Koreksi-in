export function galatDaftarDariKode(kode, pesan) {
  if (kode === "EMAIL_SUDAH_TERDAFTAR") {
    return { nama: null, email: pesan, password: null, umum: null };
  }
  if (
    kode === "PASSWORD_TERLALU_PENDEK" ||
    kode === "PASSWORD_TERLALU_PANJANG"
  ) {
    return { nama: null, email: null, password: pesan, umum: null };
  }
  return { nama: null, email: null, password: null, umum: pesan };
}

export function galatMasukDariKode(kode, pesan) {
  if (kode === "LOGIN_GAGAL") {
    return { kredensialTidakValid: true, umum: pesan };
  }
  return { kredensialTidakValid: false, umum: pesan };
}

export function fieldPertamaBermasalah(galat, urutan) {
  return urutan.find((field) => galat[field]) ?? null;
}
