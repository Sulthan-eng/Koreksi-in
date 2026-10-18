export const PESAN_KODE = {
  VALIDASI_GAGAL: "Data yang dikirim tidak valid.",
  EMAIL_SUDAH_TERDAFTAR: "Email sudah terdaftar",
  PASSWORD_TERLALU_PENDEK: "Password minimal 8 karakter",
  PASSWORD_TERLALU_PANJANG: "Password maksimal 72 karakter",
  LOGIN_GAGAL: "Email atau password salah",
  SESI_BERAKHIR: "Sesi berakhir, silakan masuk kembali.",
  BATCH_TIDAK_DITEMUKAN: "Batch tidak ditemukan",
  NAMA_BATCH_KOSONG: "Nama batch tidak boleh kosong.",
  KUNCI_KOSONG: "Kunci jawaban tidak boleh kosong",
  BATAS_SOAL_TERLAMPAUI: "Maksimal 20 soal per batch.",
  SOAL_SETELAH_JAWABAN: "Soal tidak dapat ditambah setelah jawaban diunggah.",
  GAGAL_BUAT_BATCH: "Gagal membuat batch, silakan coba lagi",
  GAGAL_TAMBAH_SOAL: "Gagal menambah soal, silakan coba lagi.",
  UMUM: "Terjadi kesalahan, silakan coba lagi.",
};

export function pesanUntukKode(kode) {
  return PESAN_KODE[kode] ?? PESAN_KODE.UMUM;
}
