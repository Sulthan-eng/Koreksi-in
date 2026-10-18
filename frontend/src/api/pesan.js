export const PESAN_KODE = {
  VALIDASI_GAGAL: "Data yang dikirim tidak valid.",
  EMAIL_SUDAH_TERDAFTAR: "Email sudah terdaftar",
  PASSWORD_TERLALU_PENDEK: "Password minimal 8 karakter",
  PASSWORD_TERLALU_PANJANG: "Password maksimal 72 karakter",
  LOGIN_GAGAL: "Email atau password salah",
  SESI_BERAKHIR: "Sesi berakhir, silakan masuk kembali.",
  UMUM: "Terjadi kesalahan, silakan coba lagi.",
};

export function pesanUntukKode(kode) {
  return PESAN_KODE[kode] ?? PESAN_KODE.UMUM;
}
