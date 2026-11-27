// Angka batas di bawah harus sama persis dengan tabel batas di docs/SPEC.md bagian 4 (dan backend/app/services/langganan.py).
export const BATAS_PER_AKUN = {
  free: { soalPerBatch: 15, jawabanPerBatch: 15 },
  pro: { soalPerBatch: 30, jawabanPerBatch: 50 },
};

export function batasSoalUntukAkun(statusLangganan) {
  return (BATAS_PER_AKUN[statusLangganan] ?? BATAS_PER_AKUN.free).soalPerBatch;
}

export function batasJawabanUntukAkun(statusLangganan) {
  return (BATAS_PER_AKUN[statusLangganan] ?? BATAS_PER_AKUN.free)
    .jawabanPerBatch;
}

export function pesanSudahMaksimalSoal(statusLangganan) {
  return `Sudah mencapai jumlah maksimal ${batasSoalUntukAkun(statusLangganan)} soal per batch.`;
}

export function pesanSisaSlotJawaban(sisa) {
  return `Sisa ${sisa} slot jawaban untuk batch ini.`;
}

export function pesanDipilihDariSlot(jumlahTerpilih, sisa) {
  return `Dipilih ${jumlahTerpilih} dari ${sisa} slot tersisa.`;
}

export function pesanMelebihiSisaSlot(sisa) {
  return `Tidak bisa menambah file: melebihi sisa slot ${sisa} jawaban untuk batch ini.`;
}

export function pesanMengirimFile(k, n) {
  return `Mengirim ${k} dari ${n} file.`;
}

export function pesanGagalTengahUnggah(tersimpan, belumTerkirim) {
  return `${tersimpan} file sudah tersimpan. ${belumTerkirim} file belum terkirim, silakan coba lagi.`;
}

export function pesanLabelHapusFile(namaFile) {
  return `Hapus ${namaFile} dari daftar`;
}

export function pesanBerlakuHingga(tanggalTeks) {
  return `Berlaku hingga ${tanggalTeks}`;
}

export function pesanNonaktifkanAkun(nama) {
  return `Akun ${nama} akan dinonaktifkan dan tidak dapat masuk. Lanjutkan?`;
}

export function pesanAktifkanAkun(nama) {
  return `Akun ${nama} akan diaktifkan dan dapat masuk kembali. Lanjutkan?`;
}

export function pesanTautanResetTerkirim(email) {
  return `Tautan atur ulang password telah dikirim ke ${email}. Periksa kotak masuk dan folder spam. Tautan berlaku 30 menit.`;
}

const KODE_PESAN_DARI_SERVER = new Set([
  "BATAS_SOAL_TERLAMPAUI",
  "BATAS_JAWABAN_TERLAMPAUI",
]);

export const PESAN_KODE = {
  VALIDASI_GAGAL: "Data yang dikirim tidak valid.",
  EMAIL_SUDAH_TERDAFTAR: "Email sudah terdaftar",
  PASSWORD_TERLALU_PENDEK: "Password minimal 8 karakter",
  PASSWORD_TERLALU_PANJANG: "Password maksimal 72 karakter",
  LOGIN_GAGAL: "Email atau password salah",
  SESI_BERAKHIR: "Sesi berakhir, silakan masuk kembali.",
  TOKEN_RESET_TIDAK_VALID: "Tautan tidak berlaku atau sudah kedaluwarsa.",
  FORMAT_EMAIL_TIDAK_VALID: "Format email tidak valid. Contoh: nama@email.com.",
  GAGAL_KIRIM_TAUTAN: "Gagal mengirim tautan, silakan coba lagi.",
  KONFIRMASI_PASSWORD_KOSONG: "Konfirmasi password wajib diisi.",
  KONFIRMASI_PASSWORD_TIDAK_SAMA: "Konfirmasi password tidak sama.",
  GAGAL_UBAH_PASSWORD: "Gagal mengubah password, silakan coba lagi.",
  PASSWORD_BERHASIL_DIUBAH: "Password berhasil diubah, silakan masuk.",
  AKSES_DITOLAK: "Anda tidak memiliki akses ke fitur ini.",
  BATCH_TIDAK_DITEMUKAN: "Batch tidak ditemukan",
  NAMA_KOSONG: "Nama wajib diisi.",
  EMAIL_KOSONG: "Email wajib diisi.",
  PASSWORD_KOSONG: "Password wajib diisi.",
  NAMA_TERLALU_PANJANG: "Nama maksimal 100 karakter.",
  EMAIL_TERLALU_PANJANG: "Email maksimal 255 karakter.",
  NAMA_BATCH_KOSONG: "Nama batch tidak boleh kosong.",
  BATAS_BATCH_AKTIF_TERCAPAI:
    "Batas batch aktif untuk akun Free telah tercapai. Upgrade ke Pro untuk batch tidak terbatas.",
  BELUM_ADA_BATCH:
    "Belum ada batch. Buat batch pertama untuk mulai mengoreksi.",
  KUNCI_KOSONG: "Kunci jawaban tidak boleh kosong",
  BATAS_SOAL_TERLAMPAUI: pesanSudahMaksimalSoal("free"),
  BATAS_JAWABAN_TERLAMPAUI: `Upload ditolak: batas jawaban akun Free adalah ${BATAS_PER_AKUN.free.jawabanPerBatch}, tersisa 0 slot. Kurangi jumlah file atau upgrade ke Pro.`,
  SOAL_SETELAH_JAWABAN: "Soal tidak dapat ditambah setelah jawaban diunggah.",
  GAGAL_BUAT_BATCH: "Gagal membuat batch, silakan coba lagi",
  GAGAL_TAMBAH_SOAL: "Gagal menambah soal, silakan coba lagi.",
  BELUM_ADA_SOAL: "Tambahkan minimal satu soal sebelum mengunggah jawaban.",
  BELUM_ADA_SOAL_BATCH: "Belum ada soal pada batch ini.",
  KUNCI_TERSIMPAN: "Kunci jawaban tersimpan.",
  SUDAH_MAKSIMAL_SOAL: pesanSudahMaksimalSoal("free"),
  PERINGATAN_SEBELUM_UNGGAH:
    "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi.",
  GAGAL_STATUS_PEMROSESAN:
    "Gagal memuat status pemrosesan, coba muat ulang halaman",
  KONEKSI_TERPUTUS: "Koneksi internet terputus, coba muat ulang halaman.",
  BELUM_ADA_HASIL_SOAL:
    "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai.",
  TEKS_OCR_KOSONG: "Teks jawaban tidak boleh kosong",
  TEKS_OCR_TERLALU_PANJANG: "Teks jawaban maksimal 10.000 karakter.",
  HASIL_KOREKSI_TIDAK_DITEMUKAN: "Hasil koreksi tidak ditemukan.",
  NILAI_AKHIR_TIDAK_VALID: "Nilai akhir harus bilangan bulat 0 sampai 100.",
  GAGAL_SIMPAN_NILAI_AKHIR:
    "Nilai gagal disimpan, silakan mencoba menyimpan kembali.",
  MAKS_FILE_TERLAMPAUI: "Maksimal 10 file per unggahan.",
  UKURAN_REQUEST_TERLALU_BESAR:
    "Total ukuran file yang dikirim terlalu besar. Kurangi jumlah file lalu coba lagi.",
  TIDAK_ADA_FILE: "Pilih minimal satu file untuk diunggah.",
  NAMA_PESERTA_KOSONG: "Nama peserta didik wajib untuk semua file",
  NAMA_PESERTA_TERLALU_PANJANG: "Nama peserta didik maksimal 100 karakter.",
  FORMAT_FILE_TIDAK_DIDUKUNG:
    "Format file tidak didukung. Gunakan PDF, PNG, atau JPG.",
  FILE_TERLALU_BESAR: "Ukuran file maksimal 10 MB.",
  PDF_TERLALU_BANYAK_HALAMAN: "PDF maksimal 15 halaman.",
  PDF_TIDAK_DAPAT_DIBACA: "File PDF rusak atau tidak dapat dibaca.",
  GAGAL_SIMPAN_JAWABAN: "Gagal menyimpan jawaban, silakan coba lagi.",
  HAPUS_FILE_BERMASALAH:
    "Hapus file yang bermasalah sebelum memulai penilaian.",
  JUDUL_BATALKAN_PILIHAN_FILE: "Batalkan Pilihan File",
  PESAN_BATALKAN_PILIHAN_FILE:
    "Semua file terpilih dan nama peserta didik yang sudah diisi akan dibuang. Lanjutkan?",
  OCR_KUNCI_GAGAL:
    "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual",
  JUDUL_GANTI_KUNCI: "Ganti Kunci Jawaban",
  PESAN_GANTI_KUNCI:
    "Isi kolom akan diganti dengan hasil baca file. Lanjutkan?",
  FILE_JAWABAN_TIDAK_DITEMUKAN: "File jawaban tidak ditemukan.",
  FILE_BUKAN_GAGAL: "File ini tidak berstatus Gagal.",
  GAGAL_COBA_LAGI: "Gagal mengirim ulang file, silakan coba lagi.",
  JUDUL_TINGGALKAN_HALAMAN: "Tinggalkan Halaman",
  PESAN_TINGGALKAN_HALAMAN:
    "Ada file yang belum diunggah. Yakin ingin meninggalkan halaman ini?",
  ADA_FILE_BELUM_UNGGAH:
    "Ada file yang belum diunggah. Unggah file tersebut atau batalkan pilihannya sebelum menyelesaikan batch.",
  MASIH_ADA_FILE_DIPROSES: "Tunggu hingga semua file selesai diproses.",
  BATCH_SUDAH_SELESAI: "Batch yang sudah selesai tidak dapat diubah lagi.",
  GAGAL_SELESAIKAN_BATCH: "Gagal menyelesaikan batch, silakan coba lagi",
  GAGAL_HAPUS_BATCH: "Gagal menghapus batch, silakan coba lagi",
  JUDUL_HAPUS_BATCH: "Hapus Batch",
  PESAN_HAPUS_BATCH:
    "Batch ini beserta seluruh data koreksi akan dihapus permanen dan tidak dapat dikembalikan. Lanjutkan?",
  JUDUL_SELESAIKAN_BATCH: "Selesaikan Batch",
  PESAN_SELESAIKAN_BATCH:
    "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?",
  BATCH_SELESAI_SUKSES: "Batch berhasil diselesaikan.",
  EKSPOR_KHUSUS_PRO:
    "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini.",
  BATCH_BELUM_ADA_JAWABAN:
    "Belum ada jawaban peserta didik pada batch ini untuk diekspor.",
  GAGAL_EKSPOR: "Gagal membuat file ekspor, silakan coba lagi",
  GAGAL_MUAT_LANGGANAN:
    "Gagal memuat status langganan, coba muat ulang halaman",
  AKUN_MEMAKAI_FREE: "Akun Anda memakai paket Free.",
  TRANSAKSI_GAGAL_DIBUAT: "Transaksi gagal dibuat, silakan coba lagi",
  GAGAL_MENCATAT_TRANSAKSI: "Gagal mencatat transaksi, silakan coba lagi",
  PEMBAYARAN_BELUM_TERKONFIRMASI:
    "Pembayaran belum terkonfirmasi. Jika sudah membayar, periksa status beberapa saat lagi.",
  GAGAL_MUAT_RINGKASAN: "Gagal memuat ringkasan, coba muat ulang halaman",
  AKUN_TIDAK_DITEMUKAN: "Akun Pengajar tidak ditemukan.",
  MASA_BERLAKU_TIDAK_VALID:
    "Masa berlaku wajib diisi dengan tanggal setelah hari ini.",
  GAGAL_UBAH_LANGGANAN: "Gagal mengubah status langganan, silakan coba lagi.",
  GAGAL_UBAH_STATUS_AKUN: "Gagal mengubah status akun, silakan coba lagi.",
  KONEKSI_TERPUTUS_COBA_LAGI: "Koneksi internet terputus, silakan coba lagi.",
  BELUM_ADA_AKUN_PENGAJAR: "Belum ada akun Pengajar yang terdaftar.",
  PENCARIAN_AKUN_KOSONG: "Tidak ada akun yang sesuai dengan pencarian.",
  GAGAL_MUAT_AKUN_PENGAJAR:
    "Gagal memuat daftar akun, coba muat ulang halaman.",
  GAGAL_MUAT_DASHBOARD_PANTAUAN:
    "Gagal memuat dashboard pantauan, coba muat ulang halaman.",
  LANGGANAN_BERHASIL_DIUBAH: "Status langganan berhasil diubah",
  AKUN_BERHASIL_DINONAKTIFKAN: "Akun berhasil dinonaktifkan",
  AKUN_BERHASIL_DIAKTIFKAN: "Akun berhasil diaktifkan",
  JUDUL_NONAKTIFKAN_AKUN: "Nonaktifkan Akun",
  JUDUL_AKTIFKAN_AKUN: "Aktifkan Akun",
  GAGAL_MUAT_PROFIL: "Gagal memuat profil, coba muat ulang halaman",
  PASSWORD_LAMA_SALAH: "Kata sandi saat ini tidak sesuai.",
  PASSWORD_BARU_SAMA:
    "Password baru tidak boleh sama dengan password saat ini.",
  GANTI_PASSWORD_TERKUNCI:
    "Terlalu banyak percobaan gagal. Coba lagi beberapa menit lagi.",
  KATA_SANDI_BERHASIL_DIUBAH:
    "Kata sandi berhasil diubah. Perangkat lain akan keluar otomatis.",
  UMUM: "Terjadi kesalahan, silakan coba lagi.",
};

export function pesanUntukKode(kode, pesanServer) {
  if (
    KODE_PESAN_DARI_SERVER.has(kode) &&
    typeof pesanServer === "string" &&
    pesanServer.trim() !== ""
  ) {
    return pesanServer;
  }
  return PESAN_KODE[kode] ?? PESAN_KODE.UMUM;
}
