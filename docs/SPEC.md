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

Status per November 2026:

- Prototipe UTS sudah berjalan di localhost: daftar akun, masuk, buat batch, ketik kunci jawaban, unggah lembar jawaban beserta nama peserta didik, pemrosesan otomatis (OCR lalu LLM-judge), lihat status pemrosesan, lihat tabel Dashboard Hasil Koreksi, keluar.
- Setelah prototipe: hapus batch (FR22) dan selesaikan batch (FR23) sudah ada, dan tampilan sudah dirombak (bagian 9 dan `docs/UI.md`, termasuk tab Status Pemrosesan yang dihapus).
- Tahap berikutnya: mengerjakan fitur yang berstatus "Belum dikerjakan" satu per satu atas permintaan pemilik proyek.

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
| FR1 | Registrasi, login, logout, reset password Pengajar. Admin login dan logout | - | Registrasi, login, logout: Selesai (validasi format email di backend 422 dan frontend). Reset password (tautan lewat email, lihat F-RESET) dan login Admin: Belum dikerjakan |
| FR2 | Status langganan di profil | UC-01 | Belum dikerjakan |
| FR3 | Buat batch | UC-02 | Selesai. Batas batch aktif akun Free ikut FR18 |
| FR4 | Kunci jawaban diketik | UC-04 | Selesai |
| FR5 | Kunci jawaban dari file | UC-04 | lolos test otomatis, menunggu konfirmasi tes manual pemilik proyek |
| FR6 | OCR file kunci | UC-04 | lolos test otomatis, menunggu konfirmasi tes manual pemilik proyek |
| FR7 | Tinjau atau edit hasil OCR kunci sebelum disimpan | UC-04 | lolos test otomatis, menunggu konfirmasi tes manual pemilik proyek |
| FR8 | Unggah jawaban peserta didik | UC-05 | Selesai. Batas jumlah jawaban per akun ikut FR18 |
| FR9 | Nama peserta didik diisi manual | UC-05 | Selesai |
| FR10 | OCR jawaban peserta didik | UC-05 | Selesai |
| FR11 | Status pemrosesan per file dan Coba Lagi manual | UC-06 | Status: Selesai (di daftar tab Soal dan Jawaban, tab Status Pemrosesan dihapus). Coba Lagi: Selesai |
| FR12 | Hitung skor kemiripan | - | Selesai |
| FR13 | Petakan skor ke kategori (ambang tetap 80 dan 40) | - | Selesai |
| FR14 | tabel Dashboard Hasil Koreksi | UC-07 | Selesai |
| FR15 | Edit teks OCR, skor dihitung ulang | UC-08 | Selesai |
| FR16 | Nilai akhir manual | UC-09 | Selesai |
| FR17 | Ekspor rekap nilai .xlsx (Pro) | UC-12 | Belum dikerjakan |
| FR18 | Batas batch aktif, soal, dan jawaban per jenis akun | UC-02, UC-04, UC-05 | Belum dikerjakan |
| FR19 | Integrasi payment gateway (Midtrans, Sandbox) | UC-10 | Belum dikerjakan |
| FR20 | Status akun otomatis dari pembayaran, beserta masa berlaku | UC-11 | Belum dikerjakan |
| FR21 | Dashboard ringkasan Pengajar | UC-13 | Belum dikerjakan |
| FR22 | Hapus batch | UC-03 | Selesai |
| FR23 | Selesaikan batch | UC-14 | Selesai |
| FR24 | Admin: daftar akun Pengajar, cari dan filter | UC-15 | Belum dikerjakan |
| FR25 | Admin: ubah status langganan dan masa berlaku | UC-16 | Belum dikerjakan |
| FR26 | Admin: nonaktifkan dan aktifkan akun | UC-17 | Belum dikerjakan |
| FR27 | Admin: Dashboard Pantauan | UC-18 | Belum dikerjakan |
| FR28 | Halaman Pemasaran | - | Selesai. Pengalihan Admin ke Dashboard Pantauan menunggu login Admin |

Konsekuensi status saat ini:

- Tabel `Transaksi_Pembayaran` belum dibuat. Kolom `Pengguna.status_langganan` dan `masa_berlaku_pro` sudah ada tetapi belum dipakai; semua Pengajar diperlakukan tanpa batas kuota akun sampai FR18 dikerjakan.
- Kolom `Pengguna.peran` dan `dinonaktifkan_pada` belum ada. Menambahnya adalah bagian dari tugas FR26 atau login Admin, lewat migrasi Alembic. Kolom `Pengguna.reset_token_hash` dan `reset_dibuat_pada` juga belum ada; ditambah saat reset password (F-RESET) dikerjakan, lewat migrasi Alembic.
- Kolom `Batch.status` sudah ada; nilai `aktif` dan `selesai` sudah dipakai (FR23 Selesai).
- Kolom `Hasil_Koreksi.skor_revisi` dan `skor_hitung_ulang` kini terpakai lewat FR15 dan FR16: `skor_revisi` diisi Pengajar lewat aksi "Ubah Nilai Akhir" (FR16), `skor_hitung_ulang` ditandai saat hitung ulang skor via judge gagal (FR15).
- Halaman daftar batch di Beranda sudah ada, karena Pengajar perlu membuka batch miliknya.

## 4. Aturan produk

Aturan umum:

- Lembar jawaban WAJIB mencantumkan nomor soal. Sistem memisahkan jawaban per soal berdasarkan nomor itu.
- Satu soal punya satu kunci berupa teks. Kunci diketik atau berasal dari OCR file kunci lalu diedit Pengajar (FR5 sampai FR7, F-KUNCI-FILE). Yang tersimpan tetap teks.
- Nomor soal dibuat sistem berurutan (1, 2, 3, dst). Tampilan per soal berjudul "Soal 1", "Soal 2".
- Soal TIDAK BOLEH ditambah setelah ada Lembar Jawaban pertama di batch itu. Pesan: "Soal tidak dapat ditambah setelah jawaban diunggah."
- Format file jawaban: PDF, PNG, JPG/JPEG. Maksimal 10 MB per file. PDF maksimal 15 halaman. Validasi berdasarkan isi file (signature byte), bukan hanya ekstensi.
- Unggahan bersifat all-or-nothing: jika satu file atau satu nama tidak valid, TOLAK seluruh unggahan, simpan apa pun tidak, dan tampilkan alasannya.
- Nama peserta didik diisi per file, tidak boleh kosong (setelah trim), maksimal 100 karakter. Nama yang sama boleh dipakai berulang.
- Maksimal 10 file per sekali unggah, untuk semua jenis akun. Backend memecah file ke grup maksimal 5 file per request OCR (bagian 8).
- Data tidak dapat diubah atau dihapus satuan: kunci jawaban, file jawaban, nama peserta didik. Kesalahan input diperbaiki dengan menghapus batch lalu membuatnya lagi (FR22, Selesai). Yang dapat diubah hanya teks hasil OCR jawaban (FR15) dan nilai akhir (FR16).
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
| `Hasil_Koreksi` | PK `id_koreksi`, `id_file` FK NOT NULL ON DELETE CASCADE, `id_soal` FK NOT NULL ON DELETE CASCADE, `teks_ocr` TEXT NOT NULL DEFAULT '', `skor_sistem` INT NULL (CHECK 0 sampai 100), `kategori` ENUM('sangat_mirip','cukup_mirip','kurang_mirip') NULL, `skor_revisi` INT NULL (CHECK 0 sampai 100; Nilai Akhir yang diisi Pengajar secara manual lewat FR16), `skor_hitung_ulang` BOOLEAN NOT NULL DEFAULT false (penanda bahwa penghitungan ulang skor setelah edit teks OCR gagal; true sampai berhasil). UNIQUE (`id_file`, `id_soal`). Tanpa kolom `alasan`, tanpa vektor, tanpa hash masukan |
| `Transaksi_Pembayaran` | Belum dibuat (migrasi saat FR19 dikerjakan). `id_transaksi` UUID PK, `id_pengguna` FK NOT NULL, `id_order` VARCHAR UNIQUE NOT NULL (ID order yang dikirim ke Midtrans), `paket` ENUM('pro_1_bulan','pro_3_bulan') NOT NULL, `nominal` INT NOT NULL (rupiah), `status` ENUM('menunggu','berhasil','gagal','kedaluwarsa') NOT NULL, `diperbarui_pada` TIMESTAMP NOT NULL, `dibuat_pada` TIMESTAMP NOT NULL DEFAULT now(). Arti status: `menunggu` (transaksi dibuat, belum dibayar), `berhasil` (dibayar, Pro aktif), `gagal` (ditolak atau dibatalkan), `kedaluwarsa` (batas bayar lewat). Nilai `nominal` mengikuti harga paket: 30000 untuk `pro_1_bulan`, 80000 untuk `pro_3_bulan`; harga disimpan di konfigurasi, bukan ditulis di banyak tempat |

Aturan data:

- `File_Jawaban.path` adalah path relatif `uploads/<id_batch>/<id_file>.<ext>` di bawah direktori unggahan dari environment variable `UPLOAD_DIR`. Nama asli file TIDAK disimpan.
- `kategori` NULL selama `skor_sistem` NULL. Kategori dihitung dari `skor_sistem` oleh satu fungsi (bagian 7), tidak ditulis di tempat lain.
- `jumlah_retry` menghitung Coba Lagi manual (F-RETRY, FR11). Retry otomatis tidak dihitung.
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
- Pengecualian (F-KUNCI-FILE, FR5-FR7): jalur OCR kunci jawaban (satu file, sinkron, tanpa judge) TIDAK memakai kebijakan retry di atas. Retry maksimal 1 kali (jeda 10 detik, bukan 10/30/60 detik 3x), tanpa retry bila kuota harian habis (sama seperti jalur lain), timeout per panggilan 50 detik (bukan 120 detik), dan seluruh panggilan (termasuk antrean semaphore) dibungkus batas waktu total 115 detik agar NFR1 (120 detik) tetap terjaga. Anggaran RPD dan semaphore maks 2 paralel tetap dipakai bersama. Lihat F-KUNCI-FILE untuk detail.

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
- Tombol "Coba Lagi" untuk file Gagal (F-RETRY, bagian 9), kolom Aksi, hanya batch Aktif.
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

**F-KUNCI-FILE (FR5, FR6, FR7, UC-04 alur alternatif, lolos test otomatis, menunggu konfirmasi tes manual pemilik proyek).** Di form "Tambah Soal" ada opsi "Upload File" (gambar atau PDF) berdampingan dengan kolom teks kunci (bukan mode terpisah). File dikirim ke OCR (satu panggilan Gemini, lewat `services/gemini.py`, dengan indikator loading), hasilnya mengisi kolom teks yang sama dan dapat diedit sebelum "Simpan Kunci Jawaban" (yang sudah ada, F-KUNCI, tetap satu-satunya aksi yang menyimpan).

Backend: `POST /api/batch/{id_batch}/soal/ocr-kunci` (login Pengajar, isolasi batch sama seperti F-KUNCI), multipart dengan **satu** field `file` (bukan daftar — desain endpoint sendiri yang membatasi satu file per panggilan, tanpa kode error terpisah untuk itu). Sukses → `{teks}`, status 200. **Stateless**: file tidak pernah ditulis ke `UPLOAD_DIR` atau database, hanya diproses lalu dibuang; tidak menyentuh tabel `Soal`. Pemeriksaan SEBELUM memanggil Gemini (hemat kuota untuk file yang pasti ditolak), memakai fungsi bersama `pastikan_bisa_tambah_soal` yang juga dipakai F-KUNCI (bukan disalin): batch Aktif (`BATCH_SUDAH_SELESAI`), belum ada lembar jawaban (`SOAL_SETELAH_JAWABAN`), belum mencapai batas soal (`BATAS_SOAL_TERLAMPAUI`). Lalu validasi file memakai ulang `baca_dan_validasi_file` dari F-UNGGAH (`TIDAK_ADA_FILE` bila kosong, `FORMAT_FILE_TIDAK_DIDUKUNG`, `FILE_TERLALU_BESAR`, `PDF_TERLALU_BANYAK_HALAMAN`, `PDF_TIDAK_DAPAT_DIBACA`). Hasil OCR kosong atau hanya spasi diperlakukan sebagai gagal, kode dan pesan sama seperti kegagalan Gemini lain: `OCR_KUNCI_GAGAL` (500) "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual" (menutupi kuota harian habis, gagal sementara setelah retry, dan gagal permanen).

Aturan waktu (NFR1, pengecualian dari kebijakan retry OCR jawaban/judge di bagian 8): OCR sinkron dengan indikator loading, total waktu maksimal 120 detik. Jalur ini memakai retry terpisah di `services/gemini.py`: maksimal **1** retry (jeda 10 detik, bukan 10/30/60 detik 3x), **tanpa** retry bila kuota harian habis (sama seperti jalur lain), dan timeout per panggilan diturunkan ke 50 detik (bukan 120 detik milik client bersama OCR jawaban/judge, yang tidak disentuh). Anggaran waktu: 50 + 10 + 50 = 110 detik, menyisakan margin 10 detik. Seluruh panggilan (termasuk antrean semaphore maks 2 paralel yang dipakai bersama OCR jawaban/judge) dibungkus batas waktu total terpisah 115 detik; jika terlampaui (misalnya semaphore penuh terus-menerus), permintaan tetap berakhir dengan `OCR_KUNCI_GAGAL` dalam 120 detik, bukan menggantung. Anggaran RPD harian tetap dipakai bersama OCR jawaban/judge (model sama), dihitung lewat fungsi yang sama.

Batas yang diketahui dan belum diselesaikan di sini: endpoint ini belum punya batas pemakaian per Pengajar (setiap panggilan "berharga" 1 dari anggaran RPD harian bersama semua pengguna). Satu Pengajar yang berulang kali memanggil OCR kunci dapat menghabiskan kuota harian bersama, berdampak ke pengguna lain. Ini ditinjau bersama FR18 (batas per jenis akun), tidak diselesaikan di tugas FR5-FR7 ini.

Frontend (`HalamanBatch.jsx`): tombol "Upload File" (ikon `upload`) di dalam form Tambah Soal, tepat di atas kolom teks kunci; spinner dan `aria-disabled` pada tombol selama OCR berjalan (bukan `disabled`, fokus tidak hilang, klik ganda tidak mengirim dua permintaan); kolom teks kunci diberi `readOnly` selama OCR berjalan (mencegah suntingan manual tertimpa hasil yang baru datang); tombol "Simpan Kunci Jawaban" memakai `aria-disabled` selama OCR berjalan juga (fokus tidak hilang) dan submit diabaikan, supaya teks lama tidak tersimpan tepat saat kolom akan diganti hasil OCR. Hasil sukses mengisi kolom teks dan memindahkan fokus ke sana untuk ditinjau. Gagal: pesan galat (`api/pesan.js`, kode `OCR_KUNCI_GAGAL`) tampil di slot galat yang sama dengan "Kunci jawaban tidak boleh kosong", kolom teks tidak berubah. Jika kolom teks kosong (atau hanya spasi) saat file dipilih, OCR langsung dijalankan tanpa dialog. Jika kolom sudah berisi teks, `DialogKonfirmasi` yang sudah ada muncul **sebelum** OCR dipanggil (bukan setelah hasil datang) dengan pesan "Isi kolom akan diganti dengan hasil baca file. Lanjutkan?" (judul usulan "Ganti Kunci Jawaban", tombol "Batal"/"Ya") — urutan ini dipilih supaya menekan "Batal" tidak pernah membuang panggilan Gemini yang sudah terkirim (kuota dihitung sebelum request dikirim). Memilih file apa pun mengosongkan nilai `<input type="file">` segera setelah `onChange` (sebelum keputusan dialog), sehingga memilih file yang sama dua kali tetap memicu `onChange`. File kunci disimpan di state terpisah dari file jawaban, sehingga tidak ikut dihitung oleh peringatan "tinggalkan halaman" milik F-UNGGAH.

**F-RETRY (FR11 bagian retry, UC-06).** Backend dan frontend lolos ujung ke ujung di localhost. Tombol "Coba Lagi" pada file berstatus Gagal mengirim ulang file itu sendiri (bukan grup aslinya) ke OCR, selalu mulai dari OCR lagi (tidak ada jalur "hanya judge" meski OCR sebelumnya sudah berhasil), dan mengubah status file itu menjadi Diproses. Tidak ada batas jumlah Coba Lagi. `File_Jawaban.jumlah_retry` bertambah satu setiap Coba Lagi manual diterima; retry otomatis (bagian 8) tidak dihitung. Tidak tersedia untuk batch Selesai.
Backend: `POST /api/batch/{id_batch}/file-jawaban/{id_file}/coba-lagi` (login Pengajar, isolasi batch sama seperti F-KUNCI) → `FileJawabanResponse` dengan `status_proses = "diproses"`, status 200. Hanya file berstatus `gagal` yang bisa dicoba ulang: peralihan `gagal` → `diproses` beserta `jumlah_retry + 1` dan pengosongan `pesan_error` dilakukan lewat satu UPDATE bersyarat (`WHERE status_proses = 'gagal'`) agar dua klik berturut-turut tidak memicu dua pemrosesan — klik kedua tidak mengubah baris apa pun dan mendapat galat yang sama seperti file bukan Gagal. Pemrosesan berjalan di latar belakang seperti unggahan (endpoint langsung merespons, lalu memanggil ulang fungsi pemrosesan yang sama persis dengan unggahan — tidak ada jalur Gemini baru); hasil koreksi memakai upsert yang sudah ada (kunci `id_file` + `id_soal`) sehingga `skor_revisi` dan `skor_hitung_ulang` tidak pernah tersentuh oleh Coba Lagi. File berstatus `diproses` atau `selesai`: 400 `FILE_BUKAN_GAGAL`. Batch Selesai: 400 `BATCH_SUDAH_SELESAI`. File tidak ada atau bukan milik batch itu: 404 `FILE_JAWABAN_TIDAK_DITEMUKAN`. Kegagalan tak terduga saat commit: 500 `GAGAL_COBA_LAGI`. Sama seperti unggahan (F-UNGGAH): jika server mati di antara commit status `diproses` dan mulainya tugas latar pemrosesan, file tertinggal berstatus `diproses` selamanya (server restart menandainya `gagal` lewat aturan bagian 8) — sifat ini tidak diselesaikan khusus oleh F-RETRY.
Frontend: tombol "Coba Lagi" (ikon `rotate-ccw`, nama aksesibel "Coba Lagi untuk {nama peserta didik}") di kolom Aksi daftar jawaban, hanya untuk file Gagal dan hanya batch Aktif. Setelah diklik, status baris berpindah ke Diproses dan polling 5 detik yang sudah ada (bagian 8, F-UNGGAH) mengambil alih; tombol tidak dirender lagi begitu baris tidak lagi Gagal. Indikator putar pada tombol selama permintaan berjalan (`aria-disabled`, fokus tidak hilang). Gagal diminta: pesan galat di bawah tombol lewat `api/pesan.js`; khusus galat `FILE_BUKAN_GAGAL` (baris sudah berubah di server, misalnya dari tab lain), daftar file jawaban dimuat ulang agar status baris sinkron. Fokus dipindah ke lencana Status baris itu (`tabIndex={-1}`) begitu tombol hilang karena baris berubah status, supaya tidak jatuh ke tubuh halaman. Aturan "Selesaikan Batch ditolak bila ada file Diproses" (F-SELESAI) tetap berlaku untuk file yang sedang dicoba ulang, tanpa kode tambahan (query status langsung ke database).

**F-EDIT-OCR (FR15, UC-08).** Di tabel Dashboard Hasil Koreksi, ikon atau tombol "Edit" pada kolom Teks OCR membuat sel dapat diedit; "Simpan" dan "Batal". Teks kosong: "Teks jawaban tidak boleh kosong". Setelah disimpan, skor dihitung ulang lewat judge dan skor serta kategori diperbarui. Jika teks tidak berubah DAN `skor_hitung_ulang` sudah false, hasil tersimpan dipakai ulang (NFR14) dan judge TIDAK dipanggil; jika teks tidak berubah TAPI `skor_hitung_ulang` masih true (percobaan hitung ulang sebelumnya gagal), judge dipanggil lagi karena Pengajar menekan "Coba lagi". Jika judge gagal: "Teks tersimpan, tetapi skor belum berhasil dihitung ulang. Coba lagi." (teks baru tetap tersimpan, skor lama tetap tampil; `skor_hitung_ulang` = true sampai berhasil). Tidak tersedia untuk batch Selesai. Backend: `PATCH /api/batch/{id_batch}/hasil/{id_koreksi}` (login Pengajar, isolasi batch sama seperti F-KUNCI), body `{teks_ocr}`, mengembalikan `{id_koreksi, teks_ocr, skor_sistem, kategori, skor_hitung_ulang}` dengan status 200 baik saat hitung ulang berhasil maupun gagal (frontend membaca pesan gagal dari `skor_hitung_ulang == true`). Batas panjang `teks_ocr`: 10.000 karakter. `id_koreksi` yang tidak ada, bukan milik batch itu, atau file induknya belum berstatus Selesai: 404 `HASIL_KOREKSI_TIDAK_DITEMUKAN`. `skor_revisi` TIDAK disentuh oleh endpoint ini. `GET /api/batch/{id_batch}/hasil` (F-DASHBOARD) juga diperluas dengan `id_koreksi` dan `skor_hitung_ulang` agar frontend punya identifier dan status untuk diedit. Frontend: tombol Edit di kolom Aksi (hanya batch Aktif) membuka area teks dengan Simpan dan Batal; hanya satu baris dapat diedit sekaligus dan dropdown Soal dinonaktifkan selama edit berlangsung.

**F-NILAI (FR16, UC-09).** Aksi "Ubah Nilai Akhir" pada baris tabel Dashboard Hasil Koreksi membuka form dengan nilai awal sama dengan Nilai Akhir yang sudah tersimpan, atau skor kemiripan bila belum pernah diisi. Validasi: angka bulat 0 sampai 100, pesan error di dekat form. Disimpan di kolom terpisah dari `skor_sistem` (yang tetap apa adanya). Nilai akhir tampil di tabel sebagai nilai resmi pada kolom "Nilai Akhir" tersendiri (skor kemiripan sistem tetap terlihat di kolom "Skor Kemiripan" sebagai rekomendasi); saat `skor_revisi` masih NULL, sel menampilkan tanda "—". Gagal simpan: "Nilai gagal disimpan, silakan mencoba menyimpan kembali." Tidak tersedia untuk batch Selesai. Tidak ada aksi untuk mengosongkan kembali Nilai Akhir yang sudah diisi. Backend: `PATCH /api/batch/{id_batch}/hasil/{id_koreksi}/nilai-akhir` (login Pengajar, isolasi batch sama seperti F-KUNCI), body `{skor_revisi}` (harus bilangan bulat 0-100, bukan desimal/boolean/string/null), mengembalikan `{id_koreksi, skor_revisi}` dengan status 200. Nilai bukan bilangan bulat 0-100: 400 `NILAI_AKHIR_TIDAK_VALID`. `id_koreksi` yang tidak ada, bukan milik batch itu, atau file induknya belum berstatus Selesai: 404 `HASIL_KOREKSI_TIDAK_DITEMUKAN` (dipakai ulang dari F-EDIT-OCR). Batch Selesai: 400 `BATCH_SUDAH_SELESAI`. Endpoint ini TIDAK menyentuh `skor_sistem`, `kategori`, `teks_ocr`, atau `skor_hitung_ulang`; sebaliknya `PATCH /api/batch/{id_batch}/hasil/{id_koreksi}` (F-EDIT-OCR) TIDAK menyentuh `skor_revisi`. Kolom `Hasil_Koreksi.skor_revisi` memakai CHECK constraint rentang 0-100 di database, sama seperti `skor_sistem`. `GET /api/batch/{id_batch}/hasil` (F-DASHBOARD) diperluas dengan `skor_revisi`. Frontend: tombol "Ubah Nilai Akhir" di kolom Aksi (hanya batch Aktif), ditumpuk di bawah tombol Edit; hanya satu baris dan satu mode (edit teks OCR ATAU ubah Nilai Akhir) dapat aktif sekaligus — tombol lain yang terpengaruh memakai `aria-disabled`.

**F-SELESAI (FR23, UC-14).** Selesai (backend dan frontend). Endpoint `POST /api/batch/{id_batch}/selesaikan` (login Pengajar, isolasi batch sama seperti F-KUNCI) → `BatchResponse` dengan `status` = `selesai`. Ditolak dengan `MASIH_ADA_FILE_DIPROSES` (400) bila masih ada file berstatus Diproses, dan dengan `BATCH_SUDAH_SELESAI` (400) bila batch sudah Selesai. Tombol "Selesaikan Batch" di Halaman Batch, dan sebagai pilihan di menu aksi (titik tiga) pada tiap baris daftar batch di Beranda (hanya untuk batch Aktif). Di Halaman Batch, jika ada file terpilih yang belum diunggah: pesan galat "Ada file yang belum diunggah. Unggah file tersebut atau batalkan pilihannya sebelum menyelesaikan batch." dan dialog konfirmasi tidak dibuka. Jika masih ada file Diproses: "Tunggu hingga semua file selesai diproses." Konfirmasi "Batch yang diselesaikan tidak dapat diubah lagi. Lanjutkan?" (Ya, Batal). Sukses: status batch menjadi Selesai, aksi ubah dinonaktifkan, tampil pesan berhasil. Gagal: "Gagal menyelesaikan batch, silakan coba lagi". Begitu `status` = `selesai`, `POST /api/batch/{id_batch}/soal` dan `POST /api/batch/{id_batch}/file-jawaban` ditolak dengan `BATCH_SUDAH_SELESAI` (400) (lihat bagian 4, batch Selesai read-only).

**F-HAPUS (FR22, UC-03).** Selesai (backend dan frontend). Endpoint `DELETE /api/batch/{id_batch}` (login Pengajar, isolasi batch sama seperti F-KUNCI) → 204. Menghapus baris `Batch` beserta turunannya lewat cascade (Soal, File_Jawaban, Hasil_Koreksi), lalu menghapus direktori fisik batch itu di bawah `UPLOAD_DIR` secara best-effort: kegagalan hapus direktori hanya dicatat di log, tidak membatalkan atau mengembalikan error (baris database sudah pasti terhapus, tidak ada jalan mundur). Berlaku untuk batch Aktif dan Selesai, dan boleh dilakukan meskipun masih ada file berstatus Diproses (berbeda dari F-SELESAI) — tugas latar yang sedang memproses batch itu tidak melempar error dan tidak menulis hasil untuk batch yang sudah hilang (dibuktikan lewat test race di `test_pemrosesan.py`). Gagal hapus baris database: `GAGAL_HAPUS_BATCH` (500). Tombol "Hapus Batch" (di menu aksi titik tiga pada tiap baris daftar batch di Beranda, dan di Halaman Batch). Konfirmasi "Batch ini beserta seluruh data koreksi akan dihapus permanen dan tidak dapat dikembalikan. Lanjutkan?" (Ya, Batal). Gagal: "Gagal menghapus batch, silakan coba lagi".

**F-LANGGANAN (FR2, FR19, FR20, UC-01, UC-10, UC-11).** Label "PRO" atau "FREE" di sebelah profil di Beranda. Gagal memuat: "Gagal memuat status langganan, coba muat ulang halaman". Halaman Langganan: status, ringkasan paket Pro (dua pilihan: 1 bulan Rp 30.000 dan 3 bulan Rp 80.000, beserta manfaat), tombol "Upgrade ke Pro" (untuk akun Pro yang masih berlaku, label "Perpanjang Pro"), "Lanjutkan ke Pembayaran", lalu redirect ke checkout Midtrans (Sandbox). Transaksi dicatat berstatus `menunggu`. Kembali ke Halaman Langganan menampilkan status transaksi. Webhook Midtrans memperbarui status (`berhasil`, `gagal`, `kedaluwarsa`; penolakan dan pembatalan dicatat sebagai `gagal`); signature divalidasi, notifikasi palsu ditolak dengan 401 tanpa mengubah apa pun (NFR8). Jika berhasil, status akun menjadi Pro dengan masa berlaku 1 atau 3 bulan sejak pembayaran dikonfirmasi, tanpa perpanjangan otomatis. Akun Pro yang masa berlakunya belum habis boleh membeli paket lagi (perpanjangan manual): masa berlaku baru adalah masa berlaku saat ini ditambah durasi paket, bukan dihitung dari hari pembayaran. Masa berlaku habis: akun kembali Free otomatis (lihat U7 dan U8). Pesan: "Transaksi gagal dibuat, silakan coba lagi", "Gagal mencatat transaksi, silakan coba lagi". Semua panggilan Midtrans HARUS lewat satu modul layanan (pola sama seperti Gemini).

**F-EKSPOR (FR17, UC-12).** Tombol "Ekspor Rekap Nilai" di Halaman Batch. Hanya akun Pro; akun Free ditolak dengan "Fitur ekspor hanya tersedia untuk akun Pro. Upgrade untuk mengakses fitur ini." disertai tautan ke Langganan. Isi file .xlsx: nama peserta didik, skor tiap soal, kategori, dan nilai akhir (jika ada). Gagal: "Gagal membuat file ekspor, silakan coba lagi".

**F-RINGKASAN (FR21, UC-13).** Di Beranda: jumlah total batch, jumlah peserta didik yang sudah dikoreksi, dan sisa kuota (hanya akun Free: sisa slot batch aktif dan sisa slot jawaban per batch). Gagal: "Gagal memuat ringkasan, coba muat ulang halaman".

**F-ADMIN (FR24 sampai FR27, UC-15 sampai UC-18).** Setelah login, Admin masuk ke Dashboard Pantauan. Navigasi Admin: Dashboard Pantauan, Akun Pengajar, Keluar.
- Akun Pengajar (FR24): tabel nama, email, status langganan, status aktif, tanggal daftar, jumlah batch; cari berdasarkan nama atau email; filter status langganan dan status aktif. Pesan: "Belum ada akun Pengajar yang terdaftar.", "Tidak ada akun yang sesuai dengan pencarian.", "Gagal memuat daftar akun, coba muat ulang halaman.", "Koneksi internet terputus, coba muat ulang halaman."
- Ubah langganan (FR25): tombol "Ubah Langganan", form status Free atau Pro; untuk Pro wajib mengisi masa berlaku. Pesan: "Status langganan berhasil diubah", "Masa berlaku wajib diisi dengan tanggal setelah hari ini.", "Gagal mengubah status langganan, silakan coba lagi.", "Koneksi internet terputus, silakan coba lagi."
- Nonaktifkan atau aktifkan (FR26): tombol menyesuaikan status akun; dialog konfirmasi menyebut nama akun dan tindakan. Menonaktifkan mencabut seluruh sesi akun; data tetap tersimpan; tidak ada penghapusan akun. Pesan: "Akun berhasil dinonaktifkan", "Akun berhasil diaktifkan", "Gagal mengubah status akun, silakan coba lagi."
- Dashboard Pantauan (FR27): jumlah akun (total, Free, Pro), jumlah batch, jumlah file jawaban per status (Diproses, Selesai, Gagal), dan pemakaian kuota API harian (dari penghitung di `services/gemini.py`, bagian 8). Hanya angka agregat. Tanpa data: tampilkan nilai 0. Gagal: "Gagal memuat dashboard pantauan, coba muat ulang halaman."

**F-PEMASARAN (FR28).** Halaman publik di alamat utama (`/`) untuk pengunjung yang belum login: penjelasan fitur, cara kerja, perbedaan akun Free dan Pro, serta tautan ke Daftar dan Masuk, dengan bilah atas varian Publik yang menempel di atas (`sticky`) beserta tiga tautan jangkar ("Cara kerja", "Fitur utama", "Free dan Pro") mulai lebar 1024 px. Isi dan rancangan visual mengikuti `docs/UI.md` bagian 1. Perilaku alamat `/` dan sesi: pengunjung tanpa sesi melihat Halaman Pemasaran; pengguna dengan sesi (Pengajar) tetap melihat Beranda di `/` seperti sebelumnya (pengalihan Admin yang sudah login ke Dashboard Pantauan menunggu FR26/login Admin dikerjakan). Setelah menekan Keluar dari halaman terproteksi mana pun, pengguna diarahkan ke `/` (Halaman Pemasaran) tanpa pesan sesi berakhir (U9). Jika sesi berakhir saat pengguna sedang berada di halaman terproteksi (termasuk Beranda di `/`), pengguna tetap diarahkan ke `/masuk` dengan pesan "Sesi berakhir, silakan masuk kembali." (U9).

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

Kode error selesaikan dan hapus batch (bagian 9, F-SELESAI, F-HAPUS):

| Kode | Status | Pesan |
|---|---|---|
| `MASIH_ADA_FILE_DIPROSES` | 400 | "Tunggu hingga semua file selesai diproses." |
| `BATCH_SUDAH_SELESAI` | 400 | "Batch yang sudah selesai tidak dapat diubah lagi." |
| `GAGAL_SELESAIKAN_BATCH` | 500 | "Gagal menyelesaikan batch, silakan coba lagi" |
| `GAGAL_HAPUS_BATCH` | 500 | "Gagal menghapus batch, silakan coba lagi" |

Kode error edit teks OCR (bagian 9, F-EDIT-OCR):

| Kode | Status | Pesan |
|---|---|---|
| `TEKS_OCR_KOSONG` | 400 | "Teks jawaban tidak boleh kosong" |
| `TEKS_OCR_TERLALU_PANJANG` | 400 | "Teks jawaban maksimal 10.000 karakter." |
| `HASIL_KOREKSI_TIDAK_DITEMUKAN` | 404 | "Hasil koreksi tidak ditemukan." |

`BATCH_SUDAH_SELESAI` dan `BATCH_TIDAK_DITEMUKAN` dipakai ulang untuk F-EDIT-OCR (batch Selesai, dan batch yang bukan milik Pengajar itu atau tidak ada).

Kode error ubah nilai akhir (bagian 9, F-NILAI):

| Kode | Status | Pesan |
|---|---|---|
| `NILAI_AKHIR_TIDAK_VALID` | 400 | "Nilai akhir harus bilangan bulat 0 sampai 100." |
| `GAGAL_SIMPAN_NILAI_AKHIR` | 500 | "Nilai gagal disimpan, silakan mencoba menyimpan kembali." |

`BATCH_SUDAH_SELESAI`, `BATCH_TIDAK_DITEMUKAN`, dan `HASIL_KOREKSI_TIDAK_DITEMUKAN` dipakai ulang untuk F-NILAI.

Kode error OCR kunci jawaban (bagian 9, F-KUNCI-FILE):

| Kode | Status | Pesan |
|---|---|---|
| `OCR_KUNCI_GAGAL` | 500 | "Gagal membaca file, silakan coba lagi atau masukkan teks secara manual" |

`BATCH_TIDAK_DITEMUKAN`, `BATCH_SUDAH_SELESAI`, `SOAL_SETELAH_JAWABAN`, `BATAS_SOAL_TERLAMPAUI` (dari F-KUNCI/F-BATCH) dan `TIDAK_ADA_FILE`, `FORMAT_FILE_TIDAK_DIDUKUNG`, `FILE_TERLALU_BESAR`, `PDF_TERLALU_BANYAK_HALAMAN`, `PDF_TIDAK_DAPAT_DIBACA` (dari F-UNGGAH) dipakai ulang untuk F-KUNCI-FILE.

Kode error Coba Lagi (bagian 9, F-RETRY):

| Kode | Status | Pesan |
|---|---|---|
| `FILE_JAWABAN_TIDAK_DITEMUKAN` | 404 | "File jawaban tidak ditemukan." |
| `FILE_BUKAN_GAGAL` | 400 | "File ini tidak berstatus Gagal." |
| `GAGAL_COBA_LAGI` | 500 | "Gagal mengirim ulang file, silakan coba lagi." |

`BATCH_SUDAH_SELESAI` dan `BATCH_TIDAK_DITEMUKAN` dipakai ulang untuk F-RETRY.

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
| 2026-11-01 | Ejaan baku: "silahkan" diganti "silakan" pada F-NILAI ("Nilai gagal disimpan, silakan mencoba menyimpan kembali.") dan pesan transaksi ("Transaksi gagal dibuat, silakan coba lagi") |
| 2026-11-02 | Tugas PR A (hapus batch backend, FR22): catat path `DELETE /api/batch/{id_batch}` di bagian 9 (F-HAPUS); tambah kode error `GAGAL_HAPUS_BATCH` di bagian 10. Keputusan: hapus boleh langsung dilakukan meski masih ada file Diproses, karena tugas latar pemrosesan selalu query ulang baris sebelum menulis dan menelan StaleDataError/ObjectDeletedError saat menandai baris yang sudah hilang — perbaikan kecil di `services/pemrosesan.py` (`_tandai_baris_gagal` menangkap `StaleDataError`/`ObjectDeletedError` dari `sqlalchemy.orm.exc` dan menelannya, bukan membiarkannya menjalar) dibuktikan lewat dua test race di `test_pemrosesan.py`. Urutan hapus: baris database dulu (dapat gagal dan dibatalkan, `GAGAL_HAPUS_BATCH`), lalu direktori fisik dihapus best-effort (gagal hanya dicatat log, tidak mengembalikan error karena data sudah pasti terhapus). Status FR22 di bagian 3 tetap "Belum dikerjakan" sampai frontend-nya ada (PR terpisah) |
| 2026-11-02 | Tugas PR A (selesaikan batch backend, FR23): catat path `POST /api/batch/{id_batch}/selesaikan` di bagian 9 (F-SELESAI); tambah 3 kode error (`MASIH_ADA_FILE_DIPROSES`, `BATCH_SUDAH_SELESAI`, `GAGAL_SELESAIKAN_BATCH`) di bagian 10; `POST .../soal` dan `POST .../file-jawaban` menolak batch Selesai dengan `BATCH_SUDAH_SELESAI` (batch Selesai read-only, bagian 4). Status FR23 di bagian 3 tetap "Belum dikerjakan" sampai frontend-nya ada (PR terpisah) |
| 2026-11-02 | PR B2 (frontend FR22 dan FR23): lencana status, tombol "Selesaikan Batch" dan "Hapus Batch" di kepala Halaman Batch (baris tombol di bawah judul pada semua lebar, sesuai mockup halaman-batch, disetujui pemilik proyek), mode baca-saja batch Selesai (daftar soal dan daftar jawaban tetap terbaca), dan aturan file terpilih belum diunggah sebelum menyelesaikan batch dengan teks baru "Ada file yang belum diunggah. Unggah file tersebut atau batalkan pilihannya sebelum menyelesaikan batch." (disetujui pemilik proyek). Status FR22 dan FR23 di bagian 3 menjadi "Selesai": backend (PR #27) dan frontend lolos ujung ke ujung di localhost |
| 2026-11-02 | Sinkronisasi status di bagian 3 dengan kode main: FR1 registrasi, login, logout Selesai (validasi format email di backend 422, PR #15, dan di frontend `lib/validasi.js`); FR4 Selesai (pesan kunci kosong dari aplikasi: form `noValidate` dan pengecekan kunci kosong `PESAN_KODE.KUNCI_KOSONG`, PR #16; kode pesan di `api/pesan.js` sudah ada dari PR #9); FR11 bagian status Selesai (status per file bertanda Lencana dan `pesan_error` di daftar `SeksiJawabanPesertaDidik`, tab Status Pemrosesan dihapus, PR #21). Bagian 1 diperbarui per November 2026: temuan pengujian prototipe dan perombakan tampilan selesai, tahap berikutnya mengerjakan fitur Belum dikerjakan satu per satu. Legenda "Perbaikan" di bagian 3 tidak lagi dipakai baris mana pun dan dipertahankan |
| 2026-11-02 | Tugas PR A (edit teks OCR backend, FR15): catat path `PATCH /api/batch/{id_batch}/hasil/{id_koreksi}` di bagian 9 (F-EDIT-OCR); tambah 3 kode error (`TEKS_OCR_KOSONG`, `TEKS_OCR_TERLALU_PANJANG`, `HASIL_KOREKSI_TIDAK_DITEMUKAN`) di bagian 10 (`BATCH_SUDAH_SELESAI` dan `BATCH_TIDAK_DITEMUKAN` dipakai ulang); `GET /api/batch/{id_batch}/hasil` diperluas dengan `id_koreksi` dan `skor_hitung_ulang`. Batas panjang `teks_ocr` 10.000 karakter (tidak ditulis di SPEC sebelumnya, ditetapkan di tugas ini). Keputusan: NFR14 (pakai ulang hasil tersimpan) hanya berlaku bila `skor_hitung_ulang` sudah false; jika teks sama tapi `skor_hitung_ulang` masih true, judge dipanggil lagi. Concurrency tanpa row lock yang menahan panggilan judge: transaksi pertama menyimpan teks baru dan menyetel `skor_hitung_ulang = true` sebelum memanggil judge (bukan hanya pada jalur gagal, agar DB tetap konsisten jika terjadi exception tak terduga), lalu transaksi kedua menulis `skor_sistem`/`kategori`/`skor_hitung_ulang = false` hanya jika `teks_ocr` di database masih sama dengan teks yang dinilai, dibuktikan lewat test race di `test_hasil_koreksi.py`. `skor_revisi` tidak disentuh. Status FR15 di bagian 3 tetap "Belum dikerjakan" sampai frontend-nya ada (PR terpisah) |
| 2026-11-02 | Tugas PR B (edit teks OCR frontend, FR15): isi kolom Aksi di Tab Dashboard Hasil Koreksi dengan tombol "Edit" membuka area teks dengan "Simpan" dan "Batal" di `TabHasilKoreksi.jsx` (bagian 9, UI.md); tambah `ubahTeksOcr` di `api/batch.js` dan 3 kode error (`TEKS_OCR_KOSONG`, `TEKS_OCR_TERLALU_PANJANG`, `HASIL_KOREKSI_TIDAK_DITEMUKAN`) di `api/pesan.js` (bagian 10). Keputusan: hanya satu baris dapat diedit sekaligus (tombol Edit baris lain `aria-disabled`); dropdown Soal memakai atribut `disabled` asli (bukan `aria-disabled`) selama ada baris yang diedit; batas 10.000 karakter divalidasi saat Simpan ditekan, bukan membatasi ketikan/tempelan; Simpan dan Batal memakai `aria-disabled` selama permintaan berjalan supaya fokus tidak hilang, Esc diabaikan saat itu; tanda "skor belum dihitung ulang" memakai `role="alert"` hanya saat baru dihasilkan oleh Simpan di sesi itu, selainnya teks biasa (semua disetujui pemilik proyek). Berpindah tab (Soal dan Jawaban ke Dashboard Hasil Koreksi) tetap membuang draf tanpa peringatan (perilaku lama `HalamanBatch.jsx` me-render tab secara kondisional, tidak diubah). Hapus anotasi "(nanti)" dari baris ikon Edit dan bullet kolom Aksi di `docs/UI.md`; kolom Nilai Akhir dan "Ubah Nilai Akhir" (FR16) tetap "(nanti)". Status FR15 di bagian 3 menjadi "Selesai": backend (PR #31) dan frontend lolos ujung ke ujung di localhost |
| 2026-11-02 | Tugas FR16 (nilai akhir manual, backend dan frontend dalam satu PR): tambah endpoint `PATCH /api/batch/{id_batch}/hasil/{id_koreksi}/nilai-akhir` (bagian 9, F-NILAI), `backend/app/services/hasil_koreksi.py` fungsi `ubah_nilai_akhir`, `backend/app/schemas/hasil_koreksi.py` (`UbahNilaiAkhirRequest`, `HasilKoreksiNilaiResponse`); tambah 2 kode error (`NILAI_AKHIR_TIDAK_VALID`, `GAGAL_SIMPAN_NILAI_AKHIR`) di bagian 10 (`BATCH_SUDAH_SELESAI`, `BATCH_TIDAK_DITEMUKAN`, `HASIL_KOREKSI_TIDAK_DITEMUKAN` dipakai ulang); `GET /api/batch/{id_batch}/hasil` diperluas dengan `skor_revisi`; migrasi Alembic `ck_hasil_koreksi_skor_revisi_range` menambah CHECK constraint rentang 0-100 pada `skor_revisi`, konsisten dengan `skor_sistem`. Keputusan: validasi tipe dan rentang dilakukan di service, bukan skema Pydantic, supaya nilai tidak valid (desimal, boolean, string, null, di luar 0-100) selalu mengembalikan 400 `NILAI_AKHIR_TIDAK_VALID`, bukan 422 generik; nilai `0` dan `100` sah dan bukan dianggap "kosong". Frontend: kolom "Nilai Akhir" baru di `TabHasilKoreksi.jsx` setelah Kategori Kualitatif (sel kosong tampil "—" dengan teks `sr-only` "Belum diisi"); tombol "Ubah Nilai Akhir" (ikon `badge-check`) ditumpuk di bawah tombol Edit di kolom Aksi; state edit digeneralisasi (`idKoreksiDiedit` + `modeEdit`) sehingga Edit teks OCR dan Ubah Nilai Akhir saling mengunci dengan `aria-disabled`, konsisten dengan kunci antar-baris FR15; tambah `ubahNilaiAkhir` di `api/batch.js` dan 2 kode error di `api/pesan.js`. Tata letak kolom dan tombol mengikuti mockup yang diberikan pemilik proyek (desktop 1280px, tablet 768px, ponsel 375px). Hapus anotasi "(nanti)" untuk Nilai Akhir dan Ubah Nilai Akhir di `docs/UI.md`. Status FR16 di bagian 3 menjadi "Selesai": backend dan frontend lolos ujung ke ujung di localhost |
| 2026-11-02 | Tugas FR11 bagian Coba Lagi (F-RETRY, backend dan frontend dalam satu PR): tambah endpoint `POST /api/batch/{id_batch}/file-jawaban/{id_file}/coba-lagi` (bagian 9, F-RETRY), `backend/app/services/file_jawaban.py` fungsi `coba_lagi_file_jawaban`; tambah 3 kode error (`FILE_JAWABAN_TIDAK_DITEMUKAN`, `FILE_BUKAN_GAGAL`, `GAGAL_COBA_LAGI`) di bagian 10 (`BATCH_SUDAH_SELESAI` dan `BATCH_TIDAK_DITEMUKAN` dipakai ulang). Keputusan pemilik proyek yang menggantikan kalimat lama F-RETRY ("mengirim ulang grup itu"): satuan Coba Lagi per FILE (bukan grup asal), selalu mulai dari OCR lagi (tidak ada jalur "hanya judge"), tanpa batas jumlah Coba Lagi; retry manual memanggil ulang `pemrosesan.proses_file_jawaban([id_file])` yang sama persis dengan jalur unggahan (tidak ada jalur Gemini baru), jadi upsert `Hasil_Koreksi` yang sudah ada otomatis menjaga `skor_revisi`/`skor_hitung_ulang`. Peralihan `gagal` → `diproses` (plus `jumlah_retry + 1` dan pengosongan `pesan_error`) memakai satu UPDATE bersyarat (`WHERE status_proses = 'gagal'`) sehingga klik ganda tidak memicu dua pemrosesan — klik kedua mendapat `FILE_BUKAN_GAGAL` yang sama seperti file yang memang bukan Gagal. Sama seperti unggahan, bila server mati di antara commit status `diproses` dan mulainya tugas latar, file tertinggal `diproses` sampai aturan restart (bagian 8) menandainya `gagal`; ini bukan hal baru dan tidak diselesaikan di tugas ini. Frontend: kolom Aksi baru berisi tombol "Coba Lagi" (ikon `rotate-ccw`) di `SeksiJawabanPesertaDidik.jsx`, hanya untuk file Gagal dan batch Aktif; `onCobaLagiSukses`/`onMuatUlangDaftarFileJawaban` di `HalamanBatch.jsx` menjaga `daftarFileJawaban` tetap sinkron (termasuk saat galat `FILE_BUKAN_GAGAL` memicu pemuatan ulang daftar); fokus dipindah ke lencana Status baris (`tabIndex={-1}`) begitu tombol hilang karena baris tidak lagi Gagal, pola baru yang dipasangkan dengan `refTombolCobaLagi`/`refStatusCobaLagi` per baris (berbeda dari pola `fokusJudulTertunda` di kepala halaman karena ada banyak baris, bukan satu tombol); tambah `cobaLagiFileJawaban` di `api/batch.js` dan 3 kode error di `api/pesan.js`. Hapus anotasi "(nanti)" untuk Coba Lagi di `docs/UI.md` (tabel ikon dan bagian daftar jawaban). Status FR11 bagian Coba Lagi di bagian 3 menjadi "Selesai": backend dan frontend lolos ujung ke ujung di localhost (dikonfirmasi pemilik proyek: status Gagal, Coba Lagi dengan kuota 0 menghasilkan Gagal lagi lalu Selesai setelah kuota dikembalikan, fokus, tampilan 375px, batch Selesai, dua tab) |
| 2026-11-02 | Tugas FR28 (Halaman Pemasaran, F-PEMASARAN, frontend): tambah `frontend/src/pages/Pemasaran.jsx` (seksi Hero dua kolom dengan ilustrasi tabel dekoratif `aria-hidden`, Cara kerja, Fitur utama `md:grid-cols-2 lg:grid-cols-4`, tabel perbandingan Free dan Pro di semua lebar, pita penutup, serta pengamat seksi aktif dan gulir otomatis untuk hash URL langsung seperti `/#fitur-utama`); perbarui `BilahAtas.jsx` varian `"publik"` (sticky, bayangan tipis saat digulir, tiga tautan jangkar "Cara kerja", "Fitur utama", "Free dan Pro" mulai 1024 px dengan `aria-current="true"` hanya pada tautan aktif, penghormatan `prefers-reduced-motion`) dan arahkan tombol Keluar (`tanganiKeluar`) ke `/`; tambah `RuteUtama` di `App.jsx` untuk `/` (dengan sesi menampilkan Beranda Pengajar, sesi berakhir mengarahkan ke `/masuk` dengan pesan, tanpa sesi menampilkan Pemasaran; pengalihan Admin menunggu FR26/login Admin) serta state `keluarSengaja` di `AuthContext.jsx` dan `TataLetakTerproteksi.jsx` agar logout dari halaman terproteksi mengarah ke `/`; lengkapi bagian Pemasaran di `docs/UI.md`. Status FR28 di bagian 3 menjadi "Selesai": frontend lolos ujung ke ujung di localhost |
| 2026-11-03 | Tugas FR5-FR7 (kunci jawaban dari file, F-KUNCI-FILE, backend dan frontend dalam satu PR): tambah endpoint `POST /api/batch/{id_batch}/soal/ocr-kunci` (bagian 9) dan kode error `OCR_KUNCI_GAGAL` (bagian 10, status 500, kode lain dipakai ulang dari F-KUNCI/F-UNGGAH); endpoint stateless (file tidak disimpan), satu panggilan Gemini per file tanpa judge. Ekstrak `pastikan_bisa_tambah_soal` di `backend/app/services/soal.py` (dipakai ulang dari `tambah_soal`) dan `baca_dan_validasi_file` di `backend/app/services/file_jawaban.py` (dipakai ulang dari `unggah_jawaban`), bukan menyalin logikanya. `backend/app/services/gemini.py` ditambah jalur retry terpisah untuk OCR kunci (bagian 8, pengecualian NFR1): `_dengan_retry_dan_anggaran` digeneralisasi dengan parameter `retry_delays` (default tidak berubah); fungsi baru `ocr_kunci` memakai `retry_delays=(10,)`, timeout per panggilan 50 detik (`http_options` khusus permintaan ini, client bersama tidak disentuh), dan dibungkus `asyncio.timeout` 115 detik yang mencakup antrean semaphore supaya total tidak melewati 120 detik walau semaphore penuh. Frontend: opsi "Upload File" di form Tambah Soal (`HalamanBatch.jsx`), berdampingan dengan kolom teks kunci (tidak pindah mode); `DialogKonfirmasi` ("Isi kolom akan diganti dengan hasil baca file. Lanjutkan?", judul usulan "Ganti Kunci Jawaban") muncul SEBELUM memanggil Gemini (bukan setelah hasil OCR datang) untuk menghindari memboroskan kuota saat pengguna menekan Batal; kolom teks kunci `readOnly` selama OCR berjalan; nilai `<input type="file">` dikosongkan segera di `onChange` sehingga file yang sama dapat dipilih ulang. Dicatat sebagai batas yang diketahui (bukan diselesaikan di PR ini): endpoint OCR kunci belum punya batas pemakaian per Pengajar, jadi satu pengguna dapat menghabiskan anggaran RPD harian bersama; ditinjau bersama FR18. Hapus anotasi "(nanti, FR5 sampai FR7)" di `docs/UI.md`. Status FR5, FR6, FR7 di bagian 3 menjadi "lolos test otomatis, menunggu konfirmasi tes manual pemilik proyek" (BUKAN "Selesai" sampai dikonfirmasi pemilik proyek) |
