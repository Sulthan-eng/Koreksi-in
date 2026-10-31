# SPEC Koreksi-in

Sumber kebutuhan untuk agent coding. Dokumen ini mencakup sistem penuh dengan status per fitur.

## 0. Cara memakai dokumen ini

- Kata HARUS dan TIDAK BOLEH berarti wajib.
- Otoritas: dokumen ini adalah satu-satunya sumber kebutuhan: apa yang boleh dikerjakan dan bagaimana. `docs/UI.md` mengatur tampilan dan `docs/STYLE.md` mengatur gaya kode; keduanya tidak boleh bertentangan dengan dokumen ini.
- Jika sesuatu yang dibutuhkan tidak ditulis di sini, BERHENTI dan tanya. Jangan menebak. Item di bagian 13 (Undecided) TIDAK BOLEH diimplementasikan berdasarkan asumsi.
- Fitur berstatus "Belum dikerjakan" (bagian 3) TIDAK BOLEH dikerjakan kecuali pemilik proyek memintanya secara eksplisit. Saat diminta, rincian teknis yang tidak tertulis di sini (endpoint, nama kolom baru, kode error) diputuskan di Plan mode dan dicatat di dokumen ini pada PR yang sama dengan kodenya.
- Sistem akan di-deploy. Selama pengembangan aplikasi dijalankan di localhost (bagian 11). Detail deploy (server, domain, HTTPS, penyimpanan unggahan, backup) belum diputuskan (U13); jangan menebaknya.

## 1. Tujuan dan status

Koreksi-in membantu Pengajar (guru atau dosen) mengoreksi jawaban esai atau jawaban singkat peserta didik. Sistem hanya memberi skor kemiripan dan kategori sebagai rekomendasi. Pengajar memegang nilai akhir. Sistem tidak pernah mengeluarkan nilai huruf. Ada dua peran: Pengajar dan Admin (Admin hanya mengelola akun Pengajar dan memantau penggunaan, tanpa akses ke isi kunci jawaban dan jawaban peserta didik).

Status per Oktober 2026:

- Prototipe UTS sudah berjalan di localhost: daftar akun, masuk, buat batch, ketik kunci jawaban, unggah lembar jawaban beserta nama peserta didik, pemrosesan otomatis (OCR lalu LLM-judge), lihat status pemrosesan, lihat tabel Dashboard Hasil Koreksi, keluar.
- Tahap berikutnya: memperbaiki temuan pengujian prototipe, merombak tampilan (bagian 9 dan `docs/UI.md`), lalu mengerjakan fitur yang berstatus "Belum dikerjakan" satu per satu atas permintaan pemilik proyek.

## 2. Glosarium dan istilah UI

Istilah UI wajib Bahasa Indonesia. Nama di kode mengikuti ERD (Indonesia), lihat bagian 5.

| Istilah UI | Nama di kode | Arti |
|---|---|---|
| Pengajar | `Pengguna.peran = 'pengajar'` | Pengguna utama yang mengoreksi. Berstatus langganan Free atau Pro |
| Admin | `Pengguna.peran = 'admin'` | Mengelola akun Pengajar dan memantau penggunaan. Dibuat developer, tidak ada menu tambah Admin |
| Peserta didik | kolom `nama_peserta_didik` | Hanya nama yang diketik Pengajar, tanpa akun |
| Batch Koreksi | tabel `Batch` | Satu sesi koreksi berisi soal dan lembar jawaban. Status Aktif atau Selesai |
| Soal | tabel `Soal` | Satu butir. Hanya menyimpan nomor dan kunci jawaban, TIDAK menyimpan teks soal |
| Kunci Jawaban | `Soal.kunci_jawaban` | Teks jawaban benar |
| Lembar Jawaban | tabel `File_Jawaban` | Satu file (foto, scan, PDF) milik satu peserta didik, boleh berisi jawaban beberapa soal |
| Hasil Koreksi | tabel `Hasil_Koreksi` | Satu baris per Lembar Jawaban per Soal |
| Skor Kemiripan | `Hasil_Koreksi.skor_sistem` | Bilangan bulat 0 sampai 100 dari LLM-judge |
| Kategori Kualitatif | `Hasil_Koreksi.kategori` | Sangat Mirip, Cukup Mirip, Kurang Mirip |
| Nilai Akhir | `Hasil_Koreksi.skor_revisi` | Nilai yang ditetapkan Pengajar secara manual (revisi sebelum ekspor), terpisah dari skor sistem. NULL berarti Pengajar belum merevisi |
| Ambang Batas | konstanta di kode | Batas skor ke kategori. Tetap, ditetapkan developer |
| Status Pemrosesan | `File_Jawaban.status_proses` | Diproses, Selesai, Gagal |
| Langganan | `Pengguna.status_langganan` | Free atau Pro. Pro berlaku 1 bulan (Rp 30.000) atau 3 bulan (Rp 80.000) tanpa perpanjangan otomatis |
| tabel Dashboard Hasil Koreksi | tab di Halaman Batch | Tulis selengkapnya, bukan sekadar "dashboard" |
| Dashboard Pantauan | halaman Admin | Halaman utama Admin |
| Halaman Pemasaran | halaman publik | Halaman pertama bagi pengunjung yang belum login |

## 3. Cakupan fitur (28 FR)

Status: **Selesai** (sudah di kode dan lolos uji), **Perbaikan** (sudah ada, ada selisih yang harus diperbaiki, lihat catatan), **Belum dikerjakan**.

| FR | Isi singkat | UC | Status |
|---|---|---|---|
| FR1 | Registrasi, login, logout, reset password Pengajar. Admin login dan logout | - | Registrasi, login, logout: Perbaikan (validasi format email). Reset password (tautan lewat email, lihat F-RESET) dan login Admin: Belum dikerjakan |
| FR2 | Status langganan di profil | UC-01 | Belum dikerjakan |
| FR3 | Buat batch | UC-02 | Selesai. Batas batch aktif akun Free ikut FR18 |
| FR4 | Kunci jawaban diketik | UC-04 | Perbaikan (pesan kunci kosong dari aplikasi, bukan bubble browser) |
| FR5 | Kunci jawaban dari file | UC-04 | Belum dikerjakan |
| FR6 | OCR file kunci | UC-04 | Belum dikerjakan |
| FR7 | Tinjau atau edit hasil OCR kunci sebelum disimpan | UC-04 | Belum dikerjakan |
| FR8 | Unggah jawaban peserta didik | UC-05 | Selesai. Batas jumlah jawaban per akun ikut FR18 |
| FR9 | Nama peserta didik diisi manual | UC-05 | Selesai |
| FR10 | OCR jawaban peserta didik | UC-05 | Selesai |
| FR11 | Status pemrosesan per file dan Coba Lagi manual | UC-06 | Status: Perbaikan (dipindah ke daftar di tab Soal dan Jawaban, tab Status Pemrosesan dihapus). Coba Lagi: Belum dikerjakan |
| FR12 | Hitung skor kemiripan | - | Selesai |
| FR13 | Petakan skor ke kategori (ambang tetap 80 dan 40) | - | Selesai |
| FR14 | tabel Dashboard Hasil Koreksi | UC-07 | Selesai |
| FR15 | Edit teks OCR, skor dihitung ulang | UC-08 | Belum dikerjakan |
| FR16 | Nilai akhir manual | UC-09 | Belum dikerjakan |
| FR17 | Ekspor rekap nilai .xlsx (Pro) | UC-12 | Belum dikerjakan |
| FR18 | Batas batch aktif, soal, dan jawaban per jenis akun | UC-02, UC-04, UC-05 | Belum dikerjakan |
| FR19 | Integrasi payment gateway (Midtrans, Sandbox) | UC-10 | Belum dikerjakan |
| FR20 | Status akun otomatis dari pembayaran, beserta masa berlaku | UC-11 | Belum dikerjakan |
| FR21 | Dashboard ringkasan Pengajar | UC-13 | Belum dikerjakan |
| FR22 | Hapus batch | UC-03 | Belum dikerjakan |
| FR23 | Selesaikan batch | UC-14 | Belum dikerjakan |
| FR24 | Admin: daftar akun Pengajar, cari dan filter | UC-15 | Belum dikerjakan |
| FR25 | Admin: ubah status langganan dan masa berlaku | UC-16 | Belum dikerjakan |
| FR26 | Admin: nonaktifkan dan aktifkan akun | UC-17 | Belum dikerjakan |
| FR27 | Admin: Dashboard Pantauan | UC-18 | Belum dikerjakan |
| FR28 | Halaman Pemasaran | - | Belum dikerjakan |

Konsekuensi status saat ini:

- Tabel `Transaksi_Pembayaran` belum dibuat. Kolom `Pengguna.status_langganan` dan `masa_berlaku_pro` sudah ada tetapi belum dipakai; semua Pengajar diperlakukan tanpa batas kuota akun sampai FR18 dikerjakan.
- Kolom `Pengguna.peran` dan `dinonaktifkan_pada` belum ada. Menambahnya adalah bagian dari tugas FR26 atau login Admin, lewat migrasi Alembic. Kolom `Pengguna.reset_token_hash` dan `reset_dibuat_pada` juga belum ada; ditambah saat reset password (F-RESET) dikerjakan, lewat migrasi Alembic.
- Kolom `Batch.status` sudah ada; hanya nilai `aktif` yang dipakai sampai FR23 dikerjakan.
- Kolom `Hasil_Koreksi.skor_revisi` dan `skor_hitung_ulang` sudah ada tetapi belum dipakai (selalu NULL dan false) sampai FR15 dan FR16 dikerjakan.
- Halaman daftar batch di Beranda sudah ada, karena Pengajar perlu membuka batch miliknya.

## 4. Aturan produk

Aturan umum:

- Lembar jawaban WAJIB mencantumkan nomor soal. Sistem memisahkan jawaban per soal berdasarkan nomor itu.
- Satu soal punya satu kunci berupa teks. Kunci diketik (sekarang) atau berasal dari OCR file kunci lalu diedit Pengajar (FR5 sampai FR7, Belum dikerjakan). Yang tersimpan tetap teks.
- Nomor soal dibuat sistem berurutan (1, 2, 3, dst). Tampilan per soal berjudul "Soal 1", "Soal 2".
- Soal TIDAK BOLEH ditambah setelah ada Lembar Jawaban pertama di batch itu. Pesan: "Soal tidak dapat ditambah setelah jawaban diunggah."
- Format file jawaban: PDF, PNG, JPG/JPEG. Maksimal 10 MB per file. PDF maksimal 15 halaman. Validasi berdasarkan isi file (signature byte), bukan hanya ekstensi.
- Unggahan bersifat all-or-nothing: jika satu file atau satu nama tidak valid, TOLAK seluruh unggahan, simpan apa pun tidak, dan tampilkan alasannya.
- Nama peserta didik diisi per file, tidak boleh kosong (setelah trim), maksimal 100 karakter. Nama yang sama boleh dipakai berulang.
- Maksimal 10 file per sekali unggah, untuk semua jenis akun. Backend memecah file ke grup maksimal 5 file per request OCR (bagian 8).
- Data tidak dapat diubah atau dihapus satuan: kunci jawaban, file jawaban, nama peserta didik. Kesalahan input diperbaiki dengan menghapus batch lalu membuatnya lagi (FR22, Belum dikerjakan). Yang dapat diubah hanya teks hasil OCR jawaban (FR15) dan nilai akhir (FR16).
- Isolasi data: Pengajar hanya dapat mengakses batch miliknya. Akses ke ID milik Pengajar lain atau ID yang tidak ada mengembalikan 404.
- Admin TIDAK BOLEH mengakses isi kunci jawaban, file jawaban, maupun hasil koreksi. Endpoint batch, soal, file jawaban, dan hasil hanya untuk peran Pengajar.
- Batch Selesai bersifat read-only: tidak bisa menambah soal, mengunggah jawaban, Coba Lagi, mengedit teks OCR, atau mengubah nilai akhir. Tetap bisa dilihat, diekspor (Pro), dan dihapus, dan tidak dihitung sebagai batch aktif.
- Privasi: pada Gemini free tier, konten yang dikirim dapat dipakai Google untuk peningkatan produk dan dibaca reviewer manusia. Cantumkan sebagai catatan di README, jangan di UI.

Batas menurut jenis akun (FR18, Belum dikerjakan):

| Batas | Free | Pro |
|---|---|---|
| Batch aktif | 1 | tidak dibatasi |
| Soal per batch | 15 | 30 |
| Jawaban peserta didik per batch | 15 | 50 |
| File per sekali unggah | 10 | 10 |
| Ekspor rekap nilai | tidak | ya |

Sampai FR18 dikerjakan, yang berlaku adalah batas prototipe: maksimal 20 soal per batch (soal ke-21 ditolak) dan tanpa batas jumlah jawaban atau batch. Saat FR18 dikerjakan, batas prototipe diganti tabel di atas dan uji batas 20 soal diperbarui.

Akun Pro yang kembali ke Free (masa berlaku habis atau diubah Admin):

- Semua data tetap tersimpan dan tetap dapat dibuka: batch, soal, jawaban, dan hasil koreksi. Tidak ada data yang dihapus atau disembunyikan karena melebihi batas.
- Batas Free (tabel di atas) berlaku apa adanya untuk aksi baru. Akun dengan lebih dari 1 batch aktif tidak dapat membuat batch baru. Batch yang jumlah soal atau jawabannya sudah melewati batas Free tidak dapat ditambah lagi. Pengajar tetap dapat melihat data batch dan menyelesaikan batch (FR23) sampai batch aktifnya sesuai batas.
- Ekspor (FR17) tidak tersedia.
- Sistem HARUS menawarkan upgrade ke Pro lagi: banner di Beranda dan Halaman Batch selama akun Free tersebut punya data di atas batas atau baru turun dari Pro, pesan penolakan aksi yang memuat tautan ke Halaman Langganan (sudah ada di F-BATCH dan F-EKSPOR), dan tombol "Upgrade ke Pro" di Halaman Langganan. Teks banner: "Masa berlaku Pro Anda telah berakhir. Upgrade ke Pro untuk membuat batch baru dan memakai semua fitur." (teks ini usulan, dapat diganti pemilik proyek).

## 5. Data

PostgreSQL 15+, SQLAlchemy 2.0 async, migrasi hanya lewat Alembic. Semua PK adalah UUID. Pola nama PK `id_<tabel>`, kecuali `File_Jawaban` (`id_file`) dan `Hasil_Koreksi` (`id_koreksi`). Nama tabel dan kolom di bawah adalah nama persis di kode dan database, dan tabel ini adalah satu-satunya sumber skema. Jika sebuah nama kolom tidak tertulis di sini, tanya.

Enum PostgreSQL native. Di SQLAlchemy pakai Python `Enum` dengan `values_callable` agar yang tersimpan adalah nilai huruf kecil seperti `free`, bukan `FREE`.

| Tabel | Kolom |
|---|---|
| `Pengguna` | `id_pengguna`, `nama` VARCHAR(100) NOT NULL, `email` VARCHAR(255) UNIQUE NOT NULL (disimpan lowercase), `password_hash` VARCHAR(255) NOT NULL (bcrypt), `status_langganan` ENUM('free','pro') NOT NULL DEFAULT 'free', `masa_berlaku_pro` TIMESTAMP NULL, `dibuat_pada` TIMESTAMP NOT NULL DEFAULT now(). Akan ditambah (belum ada): `peran` ENUM('pengajar','admin') NOT NULL (registrasi selalu mengisi 'pengajar'; Admin hanya dibuat developer) `dinonaktifkan_pada` TIMESTAMP NULL (NULL berarti akun aktif), `reset_token_hash` VARCHAR(64) NULL (hash SHA-256 token reset password; NULL berarti tidak ada permintaan reset yang berlaku) dan `reset_dibuat_pada` TIMESTAMP NULL (waktu token reset dibuat) |
| `Sesi` | `id_sesi`, `id_pengguna` FK NOT NULL ON DELETE CASCADE, `refresh_token_hash` VARCHAR(64) UNIQUE NOT NULL (SHA-256), `dibuat_pada` NOT NULL DEFAULT now(), `terakhir_dipakai_pada` NOT NULL (diisi service), `kedaluwarsa_pada` NOT NULL (diisi service), `dicabut_pada` NULL. Satu baris per login, sehingga satu akun boleh punya beberapa sesi aktif (multi-perangkat) |
| `Batch` | `id_batch`, `id_pengguna` FK NOT NULL ON DELETE CASCADE, `nama_batch` VARCHAR(100) NOT NULL, `status` ENUM('aktif','selesai') NOT NULL DEFAULT 'aktif', `dibuat_pada` NOT NULL DEFAULT now() |
| `Soal` | `id_soal`, `id_batch` FK NOT NULL ON DELETE CASCADE, `no_soal` INT NOT NULL, `kunci_jawaban` TEXT NOT NULL. UNIQUE (`id_batch`, `no_soal`). Tanpa teks soal, tanpa vektor |
| `File_Jawaban` | `id_file`, `id_batch` FK NOT NULL ON DELETE CASCADE, `nama_peserta_didik` VARCHAR(100) NOT NULL, `path` VARCHAR(255) NOT NULL, `status_proses` ENUM('diproses','selesai','gagal') NOT NULL, `pesan_error` TEXT NULL, `jumlah_retry` INT NOT NULL DEFAULT 0, `diunggah_pada` TIMESTAMP NOT NULL DEFAULT now() |
| `Hasil_Koreksi` | PK `id_koreksi`, `id_file` FK NOT NULL ON DELETE CASCADE, `id_soal` FK NOT NULL ON DELETE CASCADE, `teks_ocr` TEXT NOT NULL DEFAULT '', `skor_sistem` INT NULL (CHECK 0 sampai 100), `kategori` ENUM('sangat_mirip','cukup_mirip','kurang_mirip') NULL, `skor_revisi` INT NULL (Nilai Akhir yang diisi Pengajar secara manual; belum dipakai), `skor_hitung_ulang` BOOLEAN NOT NULL DEFAULT false (penanda bahwa penghitungan ulang skor setelah edit teks OCR gagal; true sampai berhasil; belum dipakai). UNIQUE (`id_file`, `id_soal`). Tanpa kolom `alasan`, tanpa vektor, tanpa hash masukan |
| `Transaksi_Pembayaran` | Belum dibuat (migrasi saat FR19 dikerjakan). `id_transaksi` UUID PK, `id_pengguna` FK NOT NULL, `id_order` VARCHAR UNIQUE NOT NULL (ID order yang dikirim ke Midtrans), `paket` ENUM('pro_1_bulan','pro_3_bulan') NOT NULL, `nominal` INT NOT NULL (rupiah), `status` ENUM('menunggu','berhasil','gagal','kedaluwarsa') NOT NULL, `diperbarui_pada` TIMESTAMP NOT NULL, `dibuat_pada` TIMESTAMP NOT NULL DEFAULT now(). Arti status: `menunggu` (transaksi dibuat, belum dibayar), `berhasil` (dibayar, Pro aktif), `gagal` (ditolak atau dibatalkan), `kedaluwarsa` (batas bayar lewat). Nilai `nominal` mengikuti harga paket: 30000 untuk `pro_1_bulan`, 80000 untuk `pro_3_bulan`; harga disimpan di konfigurasi, bukan ditulis di banyak tempat |

Aturan data:

- `File_Jawaban.path` adalah path relatif `uploads/<id_batch>/<id_file>.<ext>` di bawah direktori unggahan dari environment variable `UPLOAD_DIR`. Nama asli file TIDAK disimpan.
- `kategori` NULL selama `skor_sistem` NULL. Kategori dihitung dari `skor_sistem` oleh satu fungsi (bagian 7), tidak ditulis di tempat lain.
- `jumlah_retry` menghitung Coba Lagi manual (FR11, Belum dikerjakan). Retry otomatis tidak dihitung.
- Penghapusan Batch (FR22) menghapus berkas fisik oleh backend dan baris turunan lewat cascade.
- Konsistensi hasil (NFR14): jika teks jawaban dan kunci tidak berubah, hasil yang sudah tersimpan dipakai ulang dan Gemini tidak dipanggil lagi. Pembandingnya adalah `teks_ocr` yang tersimpan dengan teks baru; tidak ada kolom hash.

## 6. Autentikasi, sesi, dan peran

Aturan ini sudah ditetapkan. Implementasi manual.

- Endpoint (prefix `/api/auth`): `POST /daftar` (201, `{nama, email, password}` → `{id_pengguna, nama, email}`); `POST /masuk` (200, `{email, password}` → `{access_token}` + cookie `refresh_token`); `POST /refresh` (200, baca cookie `refresh_token` → `{access_token}` + cookie `refresh_token` diperbarui); `POST /keluar` (204, baca cookie `refresh_token` → tanpa isi, cookie dihapus); `GET /saya` (200, header `Authorization: Bearer <access_token>` → `{nama}`; ditambah `peran` dan `status_langganan` saat tugasnya dikerjakan).
- Registrasi: `nama`, `email`, `password`. Email di-trim dan di-lowercase, lalu HARUS berformat email yang valid; format tidak valid ditolak dengan `VALIDASI_GAGAL` (422). Password minimal 8 karakter dan maksimal 72 byte, disimpan sebagai hash bcrypt. Email yang sudah terdaftar ditolak dengan pesan "Email sudah terdaftar". Setelah sukses, arahkan ke halaman masuk dengan pesan "Akun berhasil dibuat, silakan masuk". Registrasi tidak membuat sesi. Registrasi selalu membuat peran Pengajar.
- Login: `email` dan `password`. Jika gagal, pesan generik "Email atau password salah" (tanpa membedakan email atau password; diputuskan tetap generik pada 31 Okt 2026 agar daftar email terdaftar tidak mudah ditebak). Jika sukses, buat satu baris `Sesi` dan kirim access token. Admin dan Pengajar memakai endpoint login yang sama.
- Access token: JWT (HS256, rahasia `SECRET_KEY` dari environment), berlaku 15 menit, berisi `id_pengguna`, `id_sesi`, `exp`. Frontend menyimpannya di memori saja (bukan localStorage).
- Refresh token: string acak (`secrets.token_urlsafe`), BUKAN JWT. Yang disimpan di `Sesi.refresh_token_hash` hanya hash SHA-256-nya. Dikirim lewat cookie `refresh_token`: httpOnly, SameSite=Lax, Path=/api/auth, masa 7 hari. Flag Secure dikendalikan environment variable `COOKIE_SECURE` (false di localhost http).
- Refresh: endpoint membaca cookie, cari `Sesi` dengan hash itu, `dicabut_pada` NULL, `kedaluwarsa_pada` belum lewat. Jika valid, set `terakhir_dipakai_pada` dan `kedaluwarsa_pada` menjadi sekarang + 7 hari (sliding), dan terbitkan access token baru. Refresh token TIDAK dirotasi. Jika tidak valid, 401.
- Setiap request ke endpoint terproteksi: verifikasi JWT, lalu cek di database bahwa `Sesi` itu belum dicabut dan belum kedaluwarsa, lalu baca `Pengguna`. Sesi yang dicabut langsung tidak berlaku.
- Logout: mengisi `dicabut_pada` pada sesi perangkat itu dan menghapus cookie. Tidak ada menu "keluar dari semua perangkat". Reset password dan penonaktifan akun (FR26) mencabut semua sesi akun.
- Frontend: saat aplikasi dibuka (termasuk reload), panggil endpoint refresh untuk memulihkan sesi. Jika access token habis atau menerima 401 pada request, panggil refresh sekali (single-flight: request paralel menunggu satu panggilan refresh yang sama), lalu ulangi request. Jika refresh gagal di halaman terproteksi, arahkan ke halaman masuk dengan pesan "Sesi berakhir, silakan masuk kembali." Saat sistem dibuka di alamat utama tanpa sesi yang valid, tampilkan Halaman Pemasaran. Setelah Pengajar atau Admin menekan Keluar, arahkan ke Halaman Pemasaran (tanpa pesan sesi berakhir).
- Semua halaman dan endpoint kecuali registrasi, login, refresh, Halaman Pemasaran, dan webhook Payment Gateway membutuhkan login.
- Peran (NFR9, Belum dikerjakan): peran diperiksa di sisi server pada SETIAP request lewat dependensi, bukan dari klaim di frontend. Endpoint Admin hanya untuk peran Admin dan menolak Pengajar dengan 403. Endpoint Pengajar menolak Admin dengan 403. Akun dengan `dinonaktifkan_pada` terisi tidak dapat masuk dan sesinya dicabut.
- Akun Admin dibuat developer lewat proses terkontrol di server (skrip, bukan menu aplikasi). Kredensial Admin TIDAK BOLEH ditulis di kode atau repository.
- Rate limit login TIDAK diterapkan. Permintaan tautan reset password hanya dibatasi oleh jeda 60 detik per akun (F-RESET).
- Reset password (FR1): lewat tautan yang dikirim ke email, tanpa tabel baru, lihat F-RESET di bagian 9. Token disimpan sebagai hash di dua kolom `Pengguna` (bagian 5), sama seperti pola refresh token di `Sesi`. Belum dikerjakan. Endpoint dan kode error diputuskan di Plan mode saat dikerjakan.

## 7. Penilaian (LLM-judge)

Keputusan 17 Okt 2026: penentu skor adalah LLM-judge `gemini-3.5-flash-lite`. Embedding dan cosine similarity sudah diuji di Spike dan gagal membedakan jawaban salah (0 dari 21 terdeteksi), sehingga TIDAK dipakai. Jangan menulis kode embedding.

- Input: pasangan (kunci jawaban, teks jawaban hasil OCR) untuk semua item dalam satu grup file, dikirim dalam SATU request dengan structured output.
- Output terstruktur per item: id item yang dikembalikan apa adanya dan `skor` (integer 0 sampai 100). Tanpa alasan.
- Skala berjangkar yang HARUS ada di prompt: 0 untuk salah; 1 sampai 39 sebagian kecil benar; 40 sampai 79 sebagian benar; 80 sampai 100 benar. Penilaian atas kebenaran isi, bukan gaya penulisan, ejaan, atau kesalahan baca OCR yang kecil.
- Jika teks jawaban kosong (jawaban untuk nomor itu tidak ditemukan), judge TIDAK dipanggil untuk item itu: `skor_sistem` = 0, `kategori` = `kurang_mirip`, `teks_ocr` = ''. UI menampilkan "(jawaban tidak ditemukan)".
- Kategori dari satu fungsi `kategori_dari_skor(skor)`: skor >= 80 `sangat_mirip` (Sangat Mirip), 40 sampai 79 `cukup_mirip` (Cukup Mirip), < 40 `kurang_mirip` (Kurang Mirip). Konstanta ini tetap dan tidak bisa diubah Pengajar.
- Skor adalah pendapat model dan dapat bervariasi antar run. Ditampilkan sebagai rekomendasi. Konsistensi untuk masukan yang sama dijaga dengan memakai ulang hasil tersimpan (bagian 5, NFR14).
- Hasil Spike untuk acuan: jawaban benar mendapat skor 95 ke atas, jawaban salah 0, jawaban sebagian tersebar luas (sekitar 20 sampai 100) dan paling rawan meleset.
- Skor untuk soal berbentuk poin dihitung atas seluruh teks jawaban, bukan per poin.

## 8. Pemrosesan

- Berjalan async dengan FastAPI `BackgroundTasks`, satu worker, tanpa Celery atau Redis. Background task membuat session database sendiri.
- Setelah unggahan lolos validasi dan tersimpan, semua file berstatus `diproses` dan pemrosesan dimulai. Respons unggahan tidak menunggu pemrosesan.
- Pengelompokan: file dibagi ke grup menurut urutan unggah. Satu grup berisi maksimal 5 file, total 10 MB, dan total 15 halaman (gambar dihitung 1 halaman). Satu file selalu muat dalam satu grup. Batas ukuran grup 10 MB karena payload dikirim ke Gemini dalam bentuk base64 yang menambah sekitar 33% ukuran.
- Per grup, dua panggilan Gemini berurutan:
  1. OCR: satu request berisi semua file dalam grup dan daftar nomor soal batch itu. Output terstruktur per file: daftar `{no_soal, teks}`. Hanya nomor soal yang ada di batch. Jika jawaban untuk suatu nomor tidak ditemukan, JANGAN dimasukkan (kosong). Model TIDAK BOLEH menebak nomor soal, termasuk pada lembar tanpa nomor (Spike: Flash-Lite menebak jika lembar tanpa nomor).
  2. Judge (bagian 7): satu request untuk semua item (file x soal) dalam grup.
- Lalu simpan `Hasil_Koreksi` untuk setiap pasangan (file, soal batch itu), idempotent (unik per file dan soal), dan ubah status file menjadi `selesai`.
- Maksimal 2 panggilan Gemini paralel (semaphore). Panggilan lain menunggu.
- Semua panggilan Gemini HARUS lewat satu modul layanan (`backend/app/services/gemini.py`). Tidak ada file lain yang mengimpor `google-genai`. Modul itu memuat fungsi OCR grup, fungsi judge grup, retry, semaphore, dan penghitung anggaran.
- Penghitung anggaran: menghitung jumlah panggilan per model per hari (hari mengikuti zona waktu America/Los_Angeles, sama dengan reset kuota Google), disimpan di memori proses (hilang saat restart, diterima untuk saat ini). Batas dari environment variable `GEMINI_RPD_LIMIT` (default 450, di bawah batas 500). Jika batas tercapai, panggilan tidak dikirim dan diperlakukan sebagai kuota harian habis (tanpa retry). Setiap panggilan dicatat di log: model, jumlah item, dan hitungan harian, tanpa isi file, teks, atau kunci. Angka pemakaian ini juga sumber "pemakaian kuota API harian" di Dashboard Pantauan Admin (FR27); tidak ada tabel baru untuk itu.
- Retry otomatis per grup: maksimal 3 kali dengan jeda 10, 30, 60 detik, hanya untuk 429 per menit dan kegagalan sementara (503, timeout). TIDAK ada retry jika kuota harian (RPD) habis. Jika kegagalan tidak dapat dibedakan dari kuota harian, perlakukan sebagai kuota harian.
- Jika sebuah grup gagal permanen: semua file di grup itu menjadi `gagal` dengan `pesan_error`, grup lain tidak terpengaruh. Jika OCR sudah berhasil tetapi judge gagal, simpan `teks_ocr` dengan `skor_sistem` NULL, file tetap `gagal`.
- Pesan `pesan_error` ditulis dalam Bahasa Indonesia, tanpa detail teknis atau kunci. Untuk 429, kuota, dan 503: "Layanan AI sedang sibuk atau kuota harian habis, coba lagi nanti." Untuk lainnya: "Gagal membaca file, silakan coba lagi."
- Saat server start, semua file berstatus `diproses` diubah menjadi `gagal` dengan pesan "Pemrosesan terhenti karena server dimulai ulang."
- Hemat API: panggilan dibatch seperti di atas, hasil disimpan sehingga tidak dihitung ulang tanpa alasan, API key hanya dari `GEMINI_API_KEY`. Semua test memakai mock Gemini, termasuk skenario yang tidak bisa dipicu dari luar (kegagalan satu grup, 503, timeout, retry 10/30/60 detik).
- Frontend polling status tiap 5 detik, hanya selama ada file `diproses` pada batch yang sedang dibuka.

## 9. Layar dan alur

Halaman dan rute lengkap ada di `docs/UI.md` (Inventaris halaman). Halaman Batch punya DUA tab: Soal dan Jawaban, dan tabel Dashboard Hasil Koreksi. Tab Status Pemrosesan DIHAPUS (diputuskan 31 Okt 2026): status tiap file tampil di daftar pada seksi Jawaban Peserta Didik. Semua teks UI Bahasa Indonesia.

Aturan form (berlaku untuk semua form): validasi masukan menghasilkan pesan dari aplikasi persis seperti tertulis di dokumen ini, ditampilkan di bawah form atau di dekat kolomnya. TIDAK BOLEH bergantung pada bubble validasi bawaan browser (misalnya atribut `required` tanpa `noValidate`).

### F-AUTH (FR1)
Mengikuti bagian 6. Beranda hanya dapat diakses setelah login. Tombol Keluar tersedia di semua halaman terproteksi.

### F-BATCH (FR3, UC-02)
Endpoint (prefix `/api/batch`, semua butuh login Pengajar): `GET /api/batch` (daftar batch milik pengguna, `dibuat_pada` terbaru dulu), `POST /api/batch` (`{nama_batch}` → `BatchResponse`), `GET /api/batch/{id_batch}` (detail satu batch).
1. Di Beranda, Pengajar melihat sapaan "Selamat datang, {nama}" dengan kalimat pendukung "Kelola batch koreksi esai Anda di sini.", daftar batch miliknya (nama, tanggal dibuat), dan tombol "Buat Batch Baru".
2. Form meminta nama batch. Pengajar menekan "Buat".
3. Sistem memvalidasi nama tidak kosong (setelah trim), membuat batch berstatus `aktif`, lalu membuka Halaman Batch yang baru.
- Nama kosong: tampilkan pesan validasi dari aplikasi ("Nama batch tidak boleh kosong."), tidak menyimpan.
- Gagal simpan: "Gagal membuat batch, silakan coba lagi", batch tidak dibuat.
- Belum ada batch: "Belum ada batch. Buat batch pertama untuk mulai mengoreksi."
- Setelah FR18: akun Free yang sudah punya 1 batch aktif ditolak dengan "Batas batch aktif untuk akun Free telah tercapai. Upgrade ke Pro untuk batch tidak terbatas." disertai tautan ke halaman Langganan.

### F-KUNCI (FR4, UC-04, hanya ketik)
Endpoint (prefix `/api/batch/{id_batch}/soal`, semua butuh login Pengajar): `GET` (daftar soal urut `no_soal`), `POST` (`{kunci_jawaban}` → `SoalResponse`, `no_soal` dibuat sistem berurutan, tidak diterima dari klien).
Di tab Soal dan Jawaban:
1. Pengajar menekan "Tambah Soal". Sistem menyiapkan "Soal N" berikutnya dengan satu kolom teks kunci jawaban.
2. Pengajar mengetik kunci dan menekan "Simpan Kunci Jawaban".
3. Sistem memvalidasi tidak kosong, menyimpan, dan menampilkan konfirmasi "Kunci jawaban tersimpan." serta menambahkan soal ke daftar. Daftar soal menampilkan nomor dan kunci jawaban (hanya baca).
- Kunci kosong atau hanya spasi: pesan dari aplikasi "Kunci jawaban tidak boleh kosong" di bawah form, tidak ada permintaan yang terkirim atau soal yang bertambah. Pesan ini tampil untuk kolom benar-benar kosong juga (bukan bubble browser).
- Soal ke-21 (atau di atas batas akun setelah FR18), atau penambahan setelah ada lembar jawaban: ditolak sesuai bagian 4.
- Gagal simpan: tampilkan pesan error, soal tidak ditambahkan, Pengajar boleh menekan Simpan lagi.
- Belum ada soal: "Belum ada soal pada batch ini."
- Sudah mencapai batas soal: tombol "Tambah Soal" diganti pesan netral "Sudah mencapai jumlah maksimal N soal per batch." (bukan membuka form lalu gagal saat disimpan).

### F-UNGGAH (FR8, FR9, FR11 bagian tampilan, UC-05, UC-06)
Endpoint (prefix `/api/batch/{id_batch}/file-jawaban`, semua butuh login Pengajar, isolasi batch sama seperti F-KUNCI): `GET` (daftar file jawaban batch itu urut `diunggah_pada` naik, masing-masing `{id_file, nama_peserta_didik, status_proses, pesan_error}`), `POST` (multipart: `files` (0-10 file) dan `nama_peserta_didik` (daftar nama sejajar urutan file) → daftar `FileJawabanResponse` yang baru dibuat, status 201).
Prasyarat: batch memiliki minimal satu soal. Tab Soal dan Jawaban dibagi dua seksi berjudul jelas: "Soal dan Kunci Jawaban" (F-KUNCI) dan "Jawaban Peserta Didik" (seksi ini):
1. Pengajar menekan "Upload Jawaban Peserta Didik" dan memilih satu sampai 10 file.
2. Sistem menampilkan daftar file terpilih, tiap file dengan kolom nama peserta didik yang masih kosong.
3. Pengajar mengisi nama untuk tiap file lalu menekan "Upload", atau menekan "Batal" untuk mengosongkan pilihan file dan kembali ke tombol "Upload Jawaban Peserta Didik".
4. Sistem memvalidasi semua nama terisi dan semua file valid (bagian 4). Jika ada yang tidak valid, tolak seluruh unggahan tanpa menyimpan apa pun dan tampilkan alasannya; daftar file tetap tampil.
5. Sistem menyimpan file dan nama, mengelompokkan, memulai pemrosesan (bagian 8), dan menampilkan status "Diproses".
Daftar file jawaban yang sudah diunggah (di seksi Jawaban Peserta Didik):
- Tiap baris: nama peserta didik dan lencana status (Diproses, Selesai, Gagal). Untuk Gagal, tampilkan `pesan_error` di bawah nama.
- Selama ada file Diproses, daftar diperbarui tiap 5 detik.
- Gagal memuat: "Gagal memuat status pemrosesan, coba muat ulang halaman", daftar tidak ditampilkan.
- Tombol "Coba Lagi" untuk file Gagal adalah FR11 bagian retry (Belum dikerjakan). Jangan dibuat.
Pesan dan keadaan:
- Nama kosong: "Nama peserta didik wajib untuk semua file".
- Lebih dari 10 file: "Maksimal 10 file per unggahan."
- Tidak ada file dipilih: "Pilih minimal satu file untuk diunggah."
- Belum ada soal: "Tambahkan minimal satu soal sebelum mengunggah jawaban." (tombol tidak dirender).
- Gagal simpan: tampilkan pesan error dan tidak ada file tersimpan (hapus berkas yang sempat tertulis). Pengajar dapat mengunggah ulang.
- Pesan sukses "Kunci jawaban tersimpan." (F-KUNCI) disembunyikan begitu batch sudah punya file jawaban.
- Sebelum ada file jawaban, tampilkan teks peringatan kecil: "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi." (hilang begitu sudah ada file jawaban).
- Konfirmasi meninggalkan halaman: jika di form unggah ada file terpilih yang belum diunggah, dan Pengajar akan meninggalkan Halaman Batch (kembali ke Beranda, berpindah halaman, atau menutup tab), tampilkan dialog "Ada file yang belum diunggah. Yakin ingin meninggalkan halaman ini?" dengan tombol "Tetap di Halaman" dan "Tinggalkan". Jika tidak ada file terpilih, TIDAK ada dialog (pemrosesan berjalan di server dan tidak ada data yang hilang).

### F-DASHBOARD (FR12, FR13, FR14, UC-07)
Endpoint `GET /api/batch/{id_batch}/hasil` (login Pengajar, isolasi batch sama seperti F-KUNCI): daftar `{id_file, nama_peserta_didik, no_soal, teks_ocr, skor_sistem, kategori}` hanya untuk `File_Jawaban` berstatus `selesai`, digabung dengan `Hasil_Koreksi` dan `Soal`, urut `diunggah_pada` naik lalu `no_soal` naik.
Tab tabel Dashboard Hasil Koreksi:
1. Sistem menampilkan pilihan soal ("Soal 1", "Soal 2", dst). Soal pertama terpilih awal.
2. Untuk soal terpilih, tabel dengan satu baris per peserta didik yang file-nya berstatus Selesai. Kolom: Peserta Didik, Teks OCR, Skor Kemiripan (0 sampai 100), Kategori Kualitatif (teks, bukan hanya warna). Teks OCR yang panjang boleh dipotong dengan opsi menampilkan lengkap.
3. Jika Pengajar memilih soal lain, tabel diganti sesuai soal itu.
- Belum ada file Selesai: "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai."
- Gagal memuat: "Koneksi internet terputus, coba muat ulang halaman."
- Tidak ada kolom alasan, tidak ada pratinjau gambar asli (U2), tidak ada nilai huruf.

### Fitur berstatus Belum dikerjakan
Bagian ini memuat aturan dan pesan fitur supaya agent tahu batasnya. Endpoint, nama kolom baru, dan kode error diputuskan di Plan mode saat fitur diminta.

**F-KUNCI-FILE (FR5, FR6, FR7, UC-04 alur alternatif).** Di form kunci jawaban ada opsi "Upload File" (gambar atau PDF). File dikirim ke OCR (lewat `services/gemini.py`, dengan indikator loading), hasilnya tampil di kolom teks yang sama dan dapat diedit sebelum "Simpan Kunci Jawaban". Gagal OCR: "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual", kolom teks tetap kosong. Gagal simpan: "Gagal menyimpan kunci jawaban, silakan coba lagi."

**F-RETRY (FR11 bagian retry, UC-06).** Tombol "Coba Lagi" pada file atau grup berstatus Gagal mengirim ulang grup itu ke OCR dan mengubah status menjadi Diproses. `File_Jawaban.jumlah_retry` bertambah. Tidak tersedia untuk batch Selesai.

**F-EDIT-OCR (FR15, UC-08).** Di tabel Dashboard Hasil Koreksi, ikon atau tombol "Edit" pada kolom Teks OCR membuat sel dapat diedit; "Simpan" dan "Batal". Teks kosong: "Teks jawaban tidak boleh kosong". Setelah disimpan, skor dihitung ulang lewat judge dan skor serta kategori diperbarui. Jika teks tidak berubah, hasil tersimpan dipakai ulang (NFR14). Jika judge gagal: "Teks tersimpan, tetapi skor belum berhasil dihitung ulang. Coba lagi." (teks baru tetap tersimpan, skor lama tetap tampil; `skor_hitung_ulang` = true sampai berhasil). Tidak tersedia untuk batch Selesai.

**F-NILAI (FR16, UC-09).** Aksi "Ubah Nilai Akhir" pada baris tabel Dashboard Hasil Koreksi membuka form dengan nilai awal sama dengan skor kemiripan. Validasi: angka 0 sampai 100, pesan error di dekat form. Disimpan di kolom terpisah dari `skor_sistem` (yang tetap apa adanya). Nilai akhir tampil di tabel sebagai nilai resmi. Gagal simpan: "Nilai gagal disimpan, silahkan mencoba menyimpan kembali." Tidak tersedia untuk batch Selesai.

**F-SELESAI (FR23, UC-14).** Tombol "Selesaikan Batch" di Halaman Batch, dan sebagai pilihan di menu aksi (titik tiga) pada tiap baris daftar batch di Beranda (hanya untuk batch Aktif). Jika masih ada file Diproses: "Tunggu hingga semua file selesai diproses." Konfirmasi "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" (Ya, Batal). Sukses: status batch menjadi Selesai, aksi ubah dinonaktifkan, tampil pesan berhasil. Gagal: "Gagal menyelesaikan batch, silakan coba lagi".

**F-HAPUS (FR22, UC-03).** Tombol "Hapus Batch" (di menu aksi titik tiga pada tiap baris daftar batch di Beranda, dan di Halaman Batch). Konfirmasi "Batch ini beserta seluruh data koreksi akan dihapus permanen dan tidak dapat dikembalikan. Lanjutkan?" (Ya, Batal). Menghapus berkas fisik dan seluruh data turunan. Berlaku untuk batch Aktif dan Selesai. Gagal: "Gagal menghapus batch, silakan coba lagi".

**F-LANGGANAN (FR2, FR19, FR20, UC-01, UC-10, UC-11).** Label "PRO" atau "FREE" di sebelah profil di Beranda. Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman". Halaman Langganan: status, ringkasan paket Pro (dua pilihan: 1 bulan Rp 30.000 dan 3 bulan Rp 80.000, beserta manfaat), tombol "Upgrade ke Pro" (untuk akun Pro yang masih berlaku, label "Perpanjang Pro"), "Lanjutkan ke Pembayaran", lalu redirect ke checkout Midtrans (Sandbox). Transaksi dicatat berstatus `menunggu`. Kembali ke Halaman Langganan menampilkan status transaksi. Webhook Midtrans memperbarui status (`berhasil`, `gagal`, `kedaluwarsa`; penolakan dan pembatalan dicatat sebagai `gagal`); signature divalidasi, notifikasi palsu ditolak dengan 401 tanpa mengubah apa pun (NFR8). Jika berhasil, status akun menjadi Pro dengan masa berlaku 1 atau 3 bulan sejak pembayaran dikonfirmasi, tanpa perpanjangan otomatis. Akun Pro yang masa berlakunya belum habis boleh membeli paket lagi (perpanjangan manual): masa berlaku baru adalah masa berlaku saat ini ditambah durasi paket, bukan dihitung dari hari pembayaran. Masa berlaku habis: akun kembali Free otomatis (lihat U7 dan U8). Pesan: "Transaksi gagal dibuat, Silahkan coba lagi", "Gagal mencatat transaksi, silakan coba lagi". Semua panggilan Midtrans HARUS lewat satu modul layanan (pola sama seperti Gemini).

**F-EKSPOR (FR17, UC-12).** Tombol "Ekspor Rekap Nilai" di Halaman Batch. Hanya akun Pro; akun Free ditolak dengan "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini." disertai tautan ke Langganan. Isi file .xlsx: nama peserta didik, skor tiap soal, kategori, dan nilai akhir (jika ada). Gagal: "Gagal membuat file ekspor, silakan coba lagi".

**F-RINGKASAN (FR21, UC-13).** Di Beranda: jumlah total batch, jumlah peserta didik yang sudah dikoreksi, dan sisa kuota (hanya akun Free: sisa slot batch aktif dan sisa slot jawaban per batch). Gagal: "Gagal memuat ringkasan, coba muat ulang halaman".

**F-ADMIN (FR24 sampai FR27, UC-15 sampai UC-18).** Setelah login, Admin masuk ke Dashboard Pantauan. Navigasi Admin: Dashboard Pantauan, Akun Pengajar, Keluar.
- Akun Pengajar (FR24): tabel nama, email, status langganan, status aktif, tanggal daftar, jumlah batch; cari berdasarkan nama atau email; filter status langganan dan status aktif. Pesan: "Belum ada akun Pengajar yang terdaftar.", "Tidak ada akun yang sesuai dengan pencarian.", "Gagal memuat daftar akun, coba muat ulang halaman.", "Koneksi internet terputus, coba muat ulang halaman."
- Ubah langganan (FR25): tombol "Ubah Langganan", form status Free atau Pro; untuk Pro wajib mengisi masa berlaku. Pesan: "Status langganan berhasil diubah", "Masa berlaku wajib diisi dengan tanggal setelah hari ini.", "Gagal mengubah status langganan, silakan coba lagi.", "Koneksi internet terputus, silakan coba lagi."
- Nonaktifkan atau aktifkan (FR26): tombol menyesuaikan status akun; dialog konfirmasi menyebut nama akun dan tindakan. Menonaktifkan mencabut seluruh sesi akun; data tetap tersimpan; tidak ada penghapusan akun. Pesan: "Akun berhasil dinonaktifkan", "Akun berhasil diaktifkan", "Gagal mengubah status akun, silakan coba lagi."
- Dashboard Pantauan (FR27): jumlah akun (total, Free, Pro), jumlah batch, jumlah file jawaban per status (Diproses, Selesai, Gagal), dan pemakaian kuota API harian (dari penghitung di `services/gemini.py`, bagian 8). Hanya angka agregat. Tanpa data: tampilkan nilai 0. Gagal: "Gagal memuat dashboard pantauan, coba muat ulang halaman."

**F-PEMASARAN (FR28).** Halaman publik di alamat utama untuk pengunjung yang belum login: penjelasan fitur, cara kerja, perbedaan akun Free dan Pro, serta tautan ke Daftar dan Masuk. Pengunjung yang sudah login diarahkan ke Beranda (Pengajar) atau Dashboard Pantauan (Admin). Isi dan rancangan visual ditentukan di `docs/UI.md` saat halaman dikerjakan.

**F-RESET (FR1, reset password, diputuskan 31 Okt 2026).** Halaman `/lupa-password` dan `/atur-ulang-password`, publik (tanpa login). Hanya untuk akun Pengajar yang aktif.
1. Di halaman Masuk ada tautan "Lupa password?" ke halaman Lupa Password.
2. Pengajar mengisi email lalu menekan "Kirim Tautan". Email di-trim dan di-lowercase, format tidak valid ditolak dengan pesan validasi dari aplikasi: "Format email tidak valid."
3. Apa pun hasilnya (email terdaftar atau tidak, akun aktif atau tidak), sistem menjawab sama: "Jika email terdaftar, tautan atur ulang password telah dikirim." Jawaban TIDAK BOLEH membedakan, agar daftar email terdaftar tidak bisa ditebak (selaras dengan pesan login generik).
4. Jika email terdaftar dan akun aktif, sistem membuat token acak (`secrets.token_urlsafe`), menyimpan HASH SHA-256-nya di `Pengguna.reset_token_hash` dan waktunya di `reset_dibuat_pada` (token asli tidak disimpan), lalu mengirim email berisi tautan ke `/atur-ulang-password?token=...`. Aturan token: berlaku 30 menit sejak `reset_dibuat_pada`; hanya dapat dipakai sekali (kedua kolom dikosongkan setelah password berhasil diganti); permintaan tautan baru MENIMPA kedua kolom sehingga tautan sebelumnya otomatis tidak sah. Jeda permintaan: jika `reset_dibuat_pada` kurang dari 60 detik yang lalu, tautan baru TIDAK dibuat dan email TIDAK dikirim, tetapi jawaban ke pengguna tetap sama seperti langkah 3 (lihat U12). Tanpa tabel baru. Kegagalan mengirim email dicatat di log (tanpa isi token) dan dijawab sama seperti langkah 3.
5. Pengajar membuka tautan dan mengisi password baru dan konfirmasinya (aturan password sama seperti registrasi: minimal 8 karakter, maksimal 72 byte) lalu menekan "Simpan Password".
6. Sukses: password diganti, SEMUA sesi akun dicabut, Pengajar diarahkan ke Masuk dengan pesan "Password berhasil diubah, silakan masuk."
- Konfirmasi tidak sama: "Konfirmasi password tidak sama."
- Password terlalu pendek atau panjang: pesan yang sama seperti registrasi ("Password minimal 8 karakter", "Password maksimal 72 karakter").
- Token kedaluwarsa, sudah dipakai, atau tidak sah: "Tautan tidak berlaku atau sudah kedaluwarsa." dengan tautan untuk meminta tautan baru.
- Gagal menyimpan: "Gagal mengubah password, silakan coba lagi."
- Semua pengiriman email HARUS lewat satu modul layanan `backend/app/services/email.py` (pola sama seperti Gemini dan Midtrans), memakai SMTP Gmail dengan App Password dari environment variable. Tidak ada file lain yang mengirim email.
- Batas ini khusus permintaan tautan reset (jeda 60 detik per akun). Rate limit login tetap tidak diterapkan (bagian 6).

## 10. Pesan error

Backend mengembalikan kode error yang stabil; frontend memetakan kode ke teks Indonesia. Teks tidak boleh membocorkan detail teknis, jejak stack, atau isi rahasia. Pesan yang sudah ditulis di bagian 4, 6, 8, dan 9 dipakai persis. Tambahan: sesi habis, "Sesi berakhir, silakan masuk kembali."

Kode error autentikasi (bagian 6):

| Kode | Status | Pesan |
|---|---|---|
| `VALIDASI_GAGAL` | 422 | "Data yang dikirim tidak valid." |
| `EMAIL_SUDAH_TERDAFTAR` | 409 | "Email sudah terdaftar" |
| `PASSWORD_TERLALU_PENDEK` | 400 | "Password minimal 8 karakter" |
| `PASSWORD_TERLALU_PANJANG` | 400 | "Password maksimal 72 karakter" |
| `LOGIN_GAGAL` | 401 | "Email atau password salah" |
| `SESI_BERAKHIR` | 401 | "Sesi berakhir, silakan masuk kembali." |

Kode error batch dan soal (bagian 4, 9):

| Kode | Status | Pesan |
|---|---|---|
| `BATCH_TIDAK_DITEMUKAN` | 404 | "Batch tidak ditemukan" |
| `NAMA_BATCH_KOSONG` | 400 | "Nama batch tidak boleh kosong." |
| `KUNCI_KOSONG` | 400 | "Kunci jawaban tidak boleh kosong" |
| `BATAS_SOAL_TERLAMPAUI` | 400 | "Maksimal 20 soal per batch." (diganti "Sudah mencapai jumlah maksimal N soal per batch." setelah FR18) |
| `SOAL_SETELAH_JAWABAN` | 400 | "Soal tidak dapat ditambah setelah jawaban diunggah." |
| `GAGAL_BUAT_BATCH` | 500 | "Gagal membuat batch, silakan coba lagi" |
| `GAGAL_TAMBAH_SOAL` | 500 | "Gagal menambah soal, silakan coba lagi." |

Kode error unggah jawaban (bagian 4, 9):

| Kode | Status | Pesan |
|---|---|---|
| `BELUM_ADA_SOAL` | 400 | "Tambahkan minimal satu soal sebelum mengunggah jawaban." |
| `MAKS_FILE_TERLAMPAUI` | 400 | "Maksimal 10 file per unggahan." |
| `TIDAK_ADA_FILE` | 400 | "Pilih minimal satu file untuk diunggah." |
| `NAMA_PESERTA_KOSONG` | 400 | "Nama peserta didik wajib untuk semua file" |
| `NAMA_PESERTA_TERLALU_PANJANG` | 400 | "Nama peserta didik maksimal 100 karakter." |
| `FORMAT_FILE_TIDAK_DIDUKUNG` | 400 | "Format file tidak didukung. Gunakan PDF, PNG, atau JPG." |
| `FILE_TERLALU_BESAR` | 400 | "Ukuran file maksimal 10 MB." |
| `PDF_TERLALU_BANYAK_HALAMAN` | 400 | "PDF maksimal 15 halaman." |
| `PDF_TIDAK_DAPAT_DIBACA` | 400 | "File PDF rusak atau tidak dapat dibaca." |
| `GAGAL_SIMPAN_JAWABAN` | 500 | "Gagal menyimpan jawaban, silakan coba lagi." |

Kegagalan jaringan atau kode error yang tidak dikenal frontend: "Terjadi kesalahan, silakan coba lagi." (tanpa detail teknis). Kode error untuk fitur Belum dikerjakan ditambahkan saat fiturnya dikerjakan.

## 11. Lingkungan pengembangan (localhost)

- Database: PostgreSQL lewat Docker Compose. Backend dan frontend dijalankan langsung di mesin pengembang.
- Backend di port 8000. Frontend (Vite) di port 5173 dengan proxy `/api` ke backend, sehingga browser hanya melihat satu origin (cookie httpOnly bekerja tanpa CORS khusus).
- Environment variable (dibuat di `.env`, contoh tanpa nilai di `.env.example`): `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, `UPLOAD_DIR`, `COOKIE_SECURE`. Ditambah saat fiturnya dikerjakan: kunci Midtrans (Sandbox); untuk reset password (F-RESET) alamat SMTP Gmail, port, akun pengirim, App Password, dan alamat dasar frontend untuk membentuk tautan. App Password Gmail memerlukan verifikasi dua langkah aktif pada akun pengirim; batas kirim Gmail cukup untuk skala tugas kuliah.
- Direktori unggahan dan `.env` masuk `.gitignore`.
- Perintah menjalankan ada di README dan `CLAUDE.md`.

## 12. Persyaratan non-fungsional

Target resmi sistem penuh (NFR1 sampai NFR17).

| NFR | Isi | Catatan |
|---|---|---|
| NFR1 | OCR satu file (sampai 10 MB) selesai maksimal 2 menit | |
| NFR2 | Satu batch 15 file selesai maksimal 30 menit (Free), 50 file maksimal 100 menit (Pro), selama kuota API tersedia | |
| NFR3 | Halaman dashboard termuat maksimal 5 detik pada 10 Mbps | |
| NFR4 | Password di-hash (bcrypt) | |
| NFR5 | HTTPS untuk semua komunikasi | Saat deploy; localhost memakai http |
| NFR6 | Isolasi data antar Pengajar | Bagian 4 |
| NFR7 | API key hanya dari environment variable | Termasuk kredensial SMTP |
| NFR8 | Validasi signature webhook Payment Gateway | Belum dikerjakan |
| NFR9 | Fitur dan endpoint Admin hanya untuk peran Admin, dicek di server tiap request | Belum dikerjakan |
| NFR10 | Operasi non-AI tetap responsif (maksimal 5 detik) sampai 50 pengguna aktif bersamaan | |
| NFR11 | Pesan error jelas bila proses gagal | |
| NFR12 | Data yang sudah berhasil diproses tetap tersimpan walau sebagian file gagal | |
| NFR13 | Backup lewat database dump dan file unggahan, dapat direstore ke instance kosong | |
| NFR14 | Skor sama untuk masukan identik, dengan memakai ulang hasil tersimpan | Bagian 5 |
| NFR15 | Dapat dipakai Pengajar non-teknis | |
| NFR16 | Indikator loading pada unggah, OCR, dan penilaian | |
| NFR17 | Responsif, dioptimalkan untuk desktop | |

Tampilan mengikuti `docs/UI.md` (Tailwind CSS, token warna dari logo, logo, kontras). Tanpa warna hardcode di komponen.

## 13. Undecided

Item di sini TIDAK BOLEH diimplementasikan berdasarkan asumsi. Angkat saat Plan mode.

| # | Hal | Keterangan |
|---|---|---|
| U1 | Nama PK `Hasil_Koreksi` | Diputuskan: mengikuti ERD final (`id_koreksi`) |
| U2 | Pratinjau gambar asli di tabel Dashboard Hasil Koreksi | Tidak ada |
| U3 | Ambang kategori ≥80 / 40–79 / <40 | Diusulkan dari hasil Spike, berlaku sampai SRS direvisi |
| U4 | Mekanisme reset password | Diputuskan 31 Okt 2026: tautan lewat email (F-RESET), SMTP Gmail, token disimpan sebagai hash di dua kolom `Pengguna`. SRS 3.2, SRS 2.5, FR1, NFR7, SDD (tabel 2.3, ERD, DFD), perlu disesuaikan (layanan email dan kolom baru belum ada di sana) |
| U5 | Kolom persis `Transaksi_Pembayaran` | Diputuskan: kolom dari ERD pemilik proyek (bagian 5); `paket` = `pro_1_bulan`, `pro_3_bulan`; `status` = `menunggu`, `berhasil`, `gagal`, `kedaluwarsa`. SDD menyebut status "dibatalkan" dan "menunggu konfirmasi"; SDD perlu disesuaikan |
| U6 | Pesan saat akun dinonaktifkan mencoba masuk | Login memakai pesan generik. Belum diputuskan apakah akun nonaktif mendapat pesan khusus |
| U7 | Perilaku data saat akun turun dari Pro ke Free dan datanya melebihi batas Free (batch aktif, soal, jawaban) | Diputuskan 31 Okt 2026: data tetap tersimpan dan dapat dibuka; batas Free berlaku untuk aksi baru; Pengajar dapat melihat dan menyelesaikan batch; sistem menawarkan upgrade lagi (bagian 4). Sisa pertanyaan: apakah edit teks OCR (FR15) dan Nilai Akhir (FR16) pada batch aktif yang melewati batas tetap boleh. Aturan di atas tidak membatasinya |
| U8 | Cara masa berlaku Pro berakhir diproses | Dihitung saat dibaca atau lewat tugas terjadwal. Keputusan teknis di Plan mode |
| U9 | Sesi berakhir di halaman terproteksi | Diputuskan 31 Okt 2026: sesi berakhir di halaman terproteksi diarahkan ke Masuk dengan pesan; Keluar (logout) dan membuka alamat utama tanpa sesi menampilkan Halaman Pemasaran (bagian 6) |
| U10 | Harga paket Pro 1 dan 3 bulan | Diputuskan 31 Okt 2026: 1 bulan Rp 30.000, 3 bulan Rp 80.000. SRS tidak menyebut harga; SRS/SDD perlu disesuaikan bila ingin mencantumkannya |
| U11 | Pemetaan `skor_revisi` dan `skor_hitung_ulang` | Diputuskan 31 Okt 2026: `skor_revisi` = Nilai Akhir manual dari Pengajar; `skor_hitung_ulang` = penanda boolean gagal hitung ulang (bagian 5) |
| U12 | Batas permintaan tautan reset password | Diputuskan 31 Okt 2026: jeda 60 detik per akun, dihitung dari `Pengguna.reset_dibuat_pada` (tahan restart server). Jawaban ke pengguna tetap sama, sehingga tidak membocorkan apakah email terdaftar |
| U13 | Rancangan deploy | Diputuskan sebagian: deploy akan memakai Docker. Sisanya DITUNDA sampai implementasi fitur selesai: penyedia dan jenis hosting (rencana awal mencoba layanan gratis), domain, HTTPS, lokasi penyimpanan unggahan, rahasia produksi, backup (NFR13). Selama U13 terbuka, agent TIDAK BOLEH membuat Dockerfile, Compose produksi, atau konfigurasi deploy. Batasan arsitektur yang harus dipenuhi hosting mana pun: backend satu instance dan satu worker (penghitung kuota Gemini di memori, `BackgroundTasks`), penyimpanan unggahan dan data database permanen (bukan disk sementara), dan instance tidak boleh tidur saat ada file `diproses` |

## 14. Changelog

| Tanggal | Perubahan |
|---|---|
| 2026-10-17 | Draf awal |
| 2026-10-17 | Maks 10 file per unggahan. Satu modul layanan Gemini dengan penghitung anggaran. Tailwind dan `docs/UI.md`. Tanpa `docs/ERD.md` |
| 2026-10-17 | Revisi: selaras SRS 38 hlm. 24 FR sebagai penyebut, 10 FR dihitung. Nama kode mengikuti ERD Indonesia. Sesi lengkap (tabel `Sesi`). Tanpa kolom alasan. Kategori Sangat/Cukup/Kurang Mirip. Kunci hanya diketik. Soal tidak dapat ditambah setelah ada jawaban |
| 2026-10-18 | Selaraskan nama dengan ERD final (SDD): `Batch.nama` → `nama_batch`; `Soal.nomor_soal` → `no_soal`; `File_Jawaban.id_file_jawaban` → `id_file`; `File_Jawaban.status_pemrosesan` → `status_proses`; tambah `File_Jawaban.diunggah_pada`; `Hasil_Koreksi.id_hasil_koreksi` → `id_koreksi`; `Hasil_Koreksi.id_file_jawaban` → `id_file`; `Hasil_Koreksi.skor_perlu_dihitung_ulang` → `skor_hitung_ulang`. U1 diputuskan |
| 2026-10-18 | Lengkapi SPEC bagian 5 dari ERD final (celah untuk K-01): panjang VARCHAR (`Pengguna.nama` 100, `Pengguna.email` 255, `Pengguna.password_hash` 255, `Batch.nama_batch` 100, `File_Jawaban.nama_peserta_didik` 100, `File_Jawaban.path` 255); semua FK (`id_pengguna`, `id_batch`, `id_soal`, `id_file`) NOT NULL; `Sesi.dibuat_pada` DEFAULT now(), `Sesi.terakhir_dipakai_pada`/`kedaluwarsa_pada` NOT NULL tanpa default; `Batch.dibuat_pada` NOT NULL DEFAULT now() |
| 2026-10-18 | Tugas A1a (autentikasi backend): catat path endpoint `/api/auth/{daftar,masuk,refresh,keluar,saya}` di bagian 6; tambah tabel kode error autentikasi (`VALIDASI_GAGAL`, `EMAIL_SUDAH_TERDAFTAR`, `PASSWORD_TERLALU_PENDEK`, `PASSWORD_TERLALU_PANJANG`, `LOGIN_GAGAL`, `SESI_BERAKHIR`) di bagian 10 |
| 2026-10-18 | Tugas A1b (autentikasi frontend): tambah di bagian 10 pesan umum frontend untuk kegagalan jaringan/kode tak dikenal: "Terjadi kesalahan, silakan coba lagi." |
| 2026-10-18 | Tugas A2 (batch dan soal backend): catat path `GET/POST /api/batch`, `GET /api/batch/{id_batch}`, `GET/POST /api/batch/{id_batch}/soal` di bagian 9 (F-BATCH, F-KUNCI); tambah 7 kode error (`BATCH_TIDAK_DITEMUKAN`, `NAMA_BATCH_KOSONG`, `KUNCI_KOSONG`, `BATAS_SOAL_TERLAMPAUI`, `SOAL_SETELAH_JAWABAN`, `GAGAL_BUAT_BATCH`, `GAGAL_TAMBAH_SOAL`) di bagian 10 |
| 2026-10-18 | Tugas A2 (batch dan soal frontend): isi Beranda (sapaan, daftar batch, form Buat Batch Baru) dan Halaman Batch (tab Soal dan Jawaban, Tambah Soal, Simpan Kunci Jawaban) di bagian 9; catat 6 teks UI baru (sapaan "Selamat datang, {nama}", "Kelola batch koreksi esai Anda di sini.", "Belum ada batch. Buat batch pertama untuk mulai mengoreksi.", "Belum ada soal pada batch ini.", "Kunci jawaban tersimpan.", "Fitur ini belum tersedia di prototipe ini."); pindahkan pesan "Sesi berakhir, silakan masuk kembali." dari `location.state` ke state `AuthContext` agar tidak hilang akibat navigasi `TataLetakTerproteksi` |
| 2026-10-18 | Tugas A2 (perbaikan UI batas soal): saat sudah 20 soal, tombol "Tambah Soal" diganti pesan "Sudah mencapai jumlah maksimal 20 soal per batch." agar Pengajar tidak membuka form kunci jawaban yang pasti ditolak |
| 2026-10-18 | Tugas A3a (unggah lembar jawaban backend): catat path `GET/POST /api/batch/{id_batch}/file-jawaban` di bagian 9 (F-UNGGAH); tambah 10 kode error (`BELUM_ADA_SOAL`, `MAKS_FILE_TERLAMPAUI`, `TIDAK_ADA_FILE`, `NAMA_PESERTA_KOSONG`, `NAMA_PESERTA_TERLALU_PANJANG`, `FORMAT_FILE_TIDAK_DIDUKUNG`, `FILE_TERLALU_BESAR`, `PDF_TERLALU_BANYAK_HALAMAN`, `PDF_TIDAK_DAPAT_DIBACA`, `GAGAL_SIMPAN_JAWABAN`) di bagian 10; tambah dependency `python-multipart` (parsing multipart FastAPI) dan `pypdf` (hitung halaman PDF). Hanya jalur unggah dan simpan, tanpa OCR/Gemini/BackgroundTasks (A3b) |
| 2026-10-18 | Tugas A3a (unggah lembar jawaban frontend): bagi tab Soal dan Jawaban jadi dua seksi berjudul "Soal dan Kunci Jawaban" dan "Jawaban Peserta Didik" di bagian 9 (F-UNGGAH); tambah teks peringatan "Pastikan semua soal sudah ditambahkan. Setelah jawaban diunggah, soal tidak dapat ditambah lagi." (tampil hanya sebelum ada file jawaban) dan lencana status "Diproses"; tombol "Tambah Soal" diganti pesan `SOAL_SETELAH_JAWABAN` begitu batch punya file jawaban |
| 2026-10-18 | Tugas A3a (perbaikan UI unggah jawaban): tambah tombol "Batal" di samping "Upload" untuk mengosongkan pilihan file; sembunyikan pesan sukses "Kunci jawaban tersimpan." begitu batch sudah punya file jawaban |
| 2026-10-18 | Tugas A3b (pemrosesan jawaban backend): tambah `backend/app/services/gemini.py` (satu-satunya pemanggil `google-genai`, model `gemini-3.5-flash-lite`, semaphore 2, anggaran harian in-memory dengan batas waktu America/Los_Angeles dari `GEMINI_RPD_LIMIT`, retry hanya untuk error sementara 3x dengan delay 10/30/60 detik, timeout eksplisit 120 detik per panggilan) dan `backend/app/services/pemrosesan.py` (pengelompokan maks 5 file/10 MB/15 halaman, OCR lalu judge per grup, `kategori_dari_skor`, upsert idempotent `Hasil_Koreksi`, validasi keluaran model: skor di luar 0-100 jadi NULL bukan di-clamp, `id_item` tak dikenal diabaikan, item yang tidak kembali dari judge jadi NULL, `no_soal` ganda dari OCR ambil entri pertama, `no_soal` di luar batch diabaikan); jadwalkan lewat `BackgroundTasks` setelah unggah (A3a); tambah lifespan startup di `main.py` yang menandai `File_Jawaban` berstatus `diproses` jadi `gagal` saat server mulai ulang; turunkan batas ukuran grup di bagian 8 dari rencana awal 15 MB ke 10 MB karena inflasi base64 pada payload Gemini; tambah dependency `google-genai`. Tanpa endpoint baru untuk `Hasil_Koreksi` dan tanpa kode error baru di bagian 10 (kegagalan pemrosesan dikomunikasikan lewat `pesan_error` yang sudah ada, bukan lewat `{kode, pesan}` HTTP sinkron) |
| 2026-10-18 | Tugas A4+A5 (status pemrosesan dan hasil koreksi backend): tambah `GET /api/batch/{id_batch}/hasil` di bagian 9 (F-DASHBOARD), `backend/app/schemas/hasil_koreksi.py` dan `backend/app/services/hasil_koreksi.py`. Tanpa kode error baru (404 `BATCH_TIDAK_DITEMUKAN` dipakai ulang) |
| 2026-10-18 | Tugas A4+A5 (tab Status Pemrosesan dan Hasil Koreksi frontend): isi tab Status Pemrosesan (daftar nama, status, `pesan_error`) dan tab Hasil Koreksi (pilihan soal, tabel per soal) di bagian 9 (F-STATUS, F-DASHBOARD); tambah polling `daftarFileJawaban` tiap 5 detik di `HalamanBatch` selama ada file `diproses`; catat teks UI baru: "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai.", "Koneksi internet terputus, coba muat ulang halaman.", "(jawaban tidak ditemukan)", "Gagal memuat status pemrosesan, coba muat ulang halaman", "Soal {n}" sebagai label pilihan soal |
| 2026-10-31 | Sinkronisasi dengan SRS v1.2 dan SDD: cakupan 28 FR dengan status per fitur; peran Pengajar dan Admin; ERD final (`peran`, `dinonaktifkan_pada`, `Transaksi_Pembayaran`, tanpa hash masukan); batas per jenis akun (FR18); aturan sesi multi-perangkat; NFR1 sampai NFR17 mengikuti SRS; aturan fitur Belum dikerjakan dari UC-03 sampai UC-18 dan FR28; U4 sampai U11 |
| 2026-10-31 | Keputusan hasil pengujian prototipe: login tetap pesan generik; tab Status Pemrosesan dihapus, status per file tampil di daftar pada tab Soal dan Jawaban; konfirmasi meninggalkan Halaman Batch hanya bila ada file terpilih yang belum diunggah; validasi format email pada registrasi (422); pesan validasi form dari aplikasi, bukan bubble browser; uji kegagalan Gemini memakai mock |
| 2026-10-31 | Putusan 6 hal terbuka: U4 reset password lewat tautan email (F-RESET, SMTP Gmail, `services/email.py`, halaman Lupa Password dan Atur Ulang Password); U5 kolom `Transaksi_Pembayaran` dari ERD dengan `paket` (`pro_1_bulan`, `pro_3_bulan`) dan `status` (`menunggu`, `berhasil`, `gagal`, `kedaluwarsa`); U7 aturan Pro turun ke Free; U9 logout dan akses tanpa sesi ke Halaman Pemasaran; U10 harga Rp 30.000 (1 bulan) dan Rp 80.000 (3 bulan); U11 `skor_revisi` dan `skor_hitung_ulang`. Tambah U12 |
| 2026-10-31 | Reset password disimpan di ERD: `Pengguna.reset_token_hash` dan `Pengguna.reset_dibuat_pada` (tanpa tabel baru). Tautan baru menimpa tautan lama, token dikosongkan setelah dipakai, jeda 60 detik per akun dihitung dari `reset_dibuat_pada`. U12 diputuskan. F-RESET dan bagian 6 disesuaikan |
| 2026-10-31 | Sistem akan di-deploy: pernyataan "hanya localhost" diganti, bagian 11 menjadi lingkungan pengembangan, tambah U13 (rancangan deploy belum diputuskan) |
| 2026-10-31 | U13 diputuskan sebagian: deploy memakai Docker, detail ditunda; catat batasan satu worker dan penyimpanan permanen |
| 2026-11-01 | Aksi "Selesaikan Batch" dan "Hapus Batch" juga tersedia dari menu titik tiga di daftar batch Beranda (F-SELESAI, F-HAPUS), selain di Halaman Batch |
| 2026-11-01 | Teks UI diindonesiakan: "Upgrade ke Pro", "batch tidak terbatas". Akun Pro yang masih berlaku boleh memperpanjang (label "Perpanjang Pro"); masa berlaku baru = masa berlaku saat ini + durasi paket |