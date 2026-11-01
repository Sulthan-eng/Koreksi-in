export const PESAN_KODE = {
  VALIDASI_GAGAL: "Data yang dikirim tidak valid.",
  EMAIL_SUDAH_TERDAFTAR: "Email sudah terdaftar",
  PASSWORD_TERLALU_PENDEK: "Password minimal 8 karakter",
  PASSWORD_TERLALU_PANJANG: "Password maksimal 72 karakter",
  LOGIN_GAGAL: "Email atau password salah",
  SESI_BERAKHIR: "Sesi berakhir, silakan masuk kembali.",
  BATCH_TIDAK_DITEMUKAN: "Batch tidak ditemukan",
  NAMA_BATCH_KOSONG: "Nama batch tidak boleh kosong.",
  BELUM_ADA_BATCH:
    "Belum ada batch. Buat batch pertama untuk mulai mengoreksi.",
  KUNCI_KOSONG: "Kunci jawaban tidak boleh kosong",
  BATAS_SOAL_TERLAMPAUI: "Maksimal 20 soal per batch.",
  SOAL_SETELAH_JAWABAN: "Soal tidak dapat ditambah setelah jawaban diunggah.",
  GAGAL_BUAT_BATCH: "Gagal membuat batch, silakan coba lagi",
  GAGAL_TAMBAH_SOAL: "Gagal menambah soal, silakan coba lagi.",
  BELUM_ADA_SOAL: "Tambahkan minimal satu soal sebelum mengunggah jawaban.",
  BELUM_ADA_SOAL_BATCH: "Belum ada soal pada batch ini.",
  KUNCI_TERSIMPAN: "Kunci jawaban tersimpan.",
  SUDAH_MAKSIMAL_SOAL: "Sudah mencapai jumlah maksimal 20 soal per batch.",
  PERINGATAN_SEBELUM_UNGGAH:
    "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi.",
  GAGAL_STATUS_PEMROSESAN:
    "Gagal memuat status pemrosesan, coba muat ulang halaman",
  KONEKSI_TERPUTUS: "Koneksi internet terputus, coba muat ulang halaman.",
  BELUM_ADA_HASIL_SOAL:
    "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai.",
  MAKS_FILE_TERLAMPAUI: "Maksimal 10 file per unggahan.",
  TIDAK_ADA_FILE: "Pilih minimal satu file untuk diunggah.",
  NAMA_PESERTA_KOSONG: "Nama peserta didik wajib untuk semua file",
  NAMA_PESERTA_TERLALU_PANJANG: "Nama peserta didik maksimal 100 karakter.",
  FORMAT_FILE_TIDAK_DIDUKUNG:
    "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
  FILE_TERLALU_BESAR: "Ukuran file maksimal 10 MB.",
  PDF_TERLALU_BANYAK_HALAMAN: "PDF maksimal 15 halaman.",
  PDF_TIDAK_DAPAT_DIBACA: "File PDF rusak atau tidak dapat dibaca.",
  GAGAL_SIMPAN_JAWABAN: "Gagal menyimpan jawaban, silakan coba lagi.",
  JUDUL_TINGGALKAN_HALAMAN: "Tinggalkan Halaman",
  PESAN_TINGGALKAN_HALAMAN:
    "Ada file yang belum diunggah. Yakin ingin meninggalkan halaman ini?",
  UMUM: "Terjadi kesalahan, silakan coba lagi.",
};

export function pesanUntukKode(kode) {
  return PESAN_KODE[kode] ?? PESAN_KODE.UMUM;
}
