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

export function galatAturUlangPasswordDariKode(kode, pesan) {
  if (
    kode === "PASSWORD_TERLALU_PENDEK" ||
    kode === "PASSWORD_TERLALU_PANJANG"
  ) {
    return { passwordBaru: pesan, konfirmasiPassword: null, umum: null };
  }
  return { passwordBaru: null, konfirmasiPassword: null, umum: pesan };
}

export function galatMasukDariKode(kode, pesan) {
  if (kode === "LOGIN_GAGAL") {
    return { kredensialTidakValid: true, umum: pesan };
  }
  return { kredensialTidakValid: false, umum: pesan };
}

export function galatUbahProfilDariKode(kode, pesan) {
  if (kode === "NAMA_KOSONG" || kode === "NAMA_TERLALU_PANJANG") {
    return { nama: pesan, umum: null };
  }
  return { nama: null, umum: pesan };
}

export function galatGantiPasswordDariKode(kode, pesan) {
  if (kode === "PASSWORD_LAMA_SALAH") {
    return { passwordLama: pesan, passwordBaru: null, umum: null };
  }
  if (
    kode === "PASSWORD_TERLALU_PENDEK" ||
    kode === "PASSWORD_TERLALU_PANJANG" ||
    kode === "PASSWORD_BARU_SAMA"
  ) {
    return { passwordLama: null, passwordBaru: pesan, umum: null };
  }
  return { passwordLama: null, passwordBaru: null, umum: pesan };
}

export function fieldPertamaBermasalah(galat, urutan) {
  return urutan.find((field) => galat[field]) ?? null;
}
