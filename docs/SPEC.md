# SPEC Koreksi-in (prototipe UTS)

Sumber kebutuhan untuk agent coding. Diturunkan dari SRS v1.0 (23 Sep 2026), keputusan setelah Spike (17 Okt 2026), dan ruang lingkup prototipe UTS.

## 0. Cara memakai dokumen ini

- Kata HARUS dan TIDAK BOLEH berarti wajib.
- Urutan otoritas: (1) dokumen ini, (2) SRS PDF hanya sebagai latar. `docs/UI.md` mengatur tampilan dan `docs/STYLE.md` mengatur gaya kode; keduanya tidak boleh bertentangan dengan dokumen ini. Jika SRS dan dokumen ini berbeda, dokumen ini menang. Contoh: SRS masih menyebut cosine similarity, di sini penentu skor adalah LLM-judge (bagian 7).
- Jika sesuatu yang dibutuhkan tidak ditulis di sini, BERHENTI dan tanya. Jangan menebak. Item di bagian 13 (Undecided) juga TIDAK BOLEH diimplementasikan berdasarkan asumsi.
- Fitur berstatus "Cadangan" atau "Di luar prototipe" (bagian 3) TIDAK BOLEH dikerjakan kecuali pemilik proyek memintanya secara eksplisit.
- Aplikasi prototipe hanya dijalankan di localhost, tidak di-deploy (bagian 11).

## 1. Tujuan dan cakupan

Koreksi-in membantu Pengajar (guru atau dosen) mengoreksi jawaban esai atau jawaban singkat peserta didik. Sistem hanya memberi skor kemiripan dan kategori sebagai rekomendasi. Pengajar memegang nilai akhir. Sistem tidak pernah mengeluarkan nilai huruf.

Prototipe UTS (batas Minggu 18 Okt 2026, 23.59 WITA) mencakup satu alur ujung ke ujung dan HARUS berjalan tanpa bug di localhost:

daftar akun, masuk, buat batch, ketik kunci jawaban per soal, unggah lembar jawaban beserta nama peserta didik, pemrosesan otomatis (OCR lalu LLM-judge), lihat status pemrosesan, lihat tabel Dashboard Hasil Koreksi, keluar.

## 2. Glosarium dan istilah UI

Istilah UI wajib Bahasa Indonesia. Nama di kode mengikuti ERD (Indonesia), lihat bagian 5.

| Istilah UI | Nama di kode | Arti |
|---|---|---|
| Pengajar | tabel `Pengguna` | Satu-satunya peran. Tidak ada Admin |
| Peserta didik | kolom `nama_peserta_didik` | Hanya nama yang diketik Pengajar, tanpa akun |
| Batch Koreksi | tabel `Batch` | Satu sesi koreksi berisi soal dan lembar jawaban |
| Soal | tabel `Soal` | Satu butir. Hanya menyimpan nomor dan kunci jawaban, TIDAK menyimpan teks soal |
| Kunci Jawaban | `Soal.kunci_jawaban` | Teks jawaban benar, diketik Pengajar |
| Lembar Jawaban | tabel `File_Jawaban` | Satu file (foto, scan, PDF) milik satu peserta didik, boleh berisi jawaban beberapa soal |
| Hasil Koreksi | tabel `Hasil_Koreksi` | Satu baris per Lembar Jawaban per Soal |
| Skor Kemiripan | `Hasil_Koreksi.skor_sistem` | Bilangan bulat 0 sampai 100 dari LLM-judge |
| Kategori Kualitatif | `Hasil_Koreksi.kategori` | Sangat Mirip, Cukup Mirip, Kurang Mirip |
| Ambang Batas | konstanta di kode | Batas skor ke kategori. Tetap, ditetapkan developer |
| Status Pemrosesan | `File_Jawaban.status_proses` | Diproses, Selesai, Gagal |
| tabel Dashboard Hasil Koreksi | tab di halaman batch | Tulis selengkapnya, bukan sekadar "dashboard" |

## 3. Cakupan fitur (penyebut: 24 FR di SRS)

Dihitung untuk UTS: 10 dari 24 FR = 41,7% (minimum dosen 30%).

| FR | Isi singkat | Status |
|---|---|---|
| FR1 | Registrasi, login, logout, reset password | Prototipe, sebagian: TANPA reset password |
| FR2 | Status langganan | Di luar prototipe |
| FR3 | Buat batch | Prototipe |
| FR4 | Kunci jawaban diketik | Prototipe |
| FR5 | Kunci jawaban dari file | Di luar prototipe |
| FR6 | OCR file kunci | Di luar prototipe |
| FR7 | Tinjau hasil OCR kunci | Di luar prototipe |
| FR8 | Unggah jawaban peserta didik | Prototipe |
| FR9 | Nama peserta didik diisi manual | Prototipe |
| FR10 | OCR jawaban peserta didik | Prototipe |
| FR11 | Status pemrosesan + retry manual | Status DITAMPILKAN (bagian 9, F-STATUS). Tombol Coba Lagi adalah Cadangan |
| FR12 | Hitung skor kemiripan | Prototipe |
| FR13 | Petakan skor ke kategori | Prototipe |
| FR14 | Ambang batas tetap | Prototipe |
| FR15 | tabel Dashboard Hasil Koreksi | Prototipe |
| FR16 | Edit teks OCR | Cadangan |
| FR17 | Nilai akhir manual | Cadangan |
| FR18 | Ekspor .xlsx | Di luar prototipe |
| FR19 | Batas akun Free | Di luar prototipe (tidak diterapkan) |
| FR20 | Integrasi pembayaran | Di luar prototipe |
| FR21 | Status akun otomatis dari pembayaran | Di luar prototipe |
| FR22 | Dashboard ringkasan | Di luar prototipe |
| FR23 | Hapus batch | Cadangan |
| FR24 | Selesaikan batch | Di luar prototipe |

Urutan jika ada waktu sisa dan pemilik proyek meminta: (1) FR11 tombol Coba Lagi, (2) FR17, (3) FR23, (4) FR16. Reset password tidak dikerjakan.

Konsekuensi lingkup:
- Tabel `Transaksi_Pembayaran` TIDAK dibuat. Kolom `Pengguna.status_langganan` dan `Pengguna.masa_berlaku_pro` dibuat sesuai ERD tetapi TIDAK dipakai. Semua pengguna diperlakukan tanpa batas kuota.
- Kolom `Batch.status` dibuat; hanya nilai `aktif` yang dipakai.
- Kolom `Hasil_Koreksi.skor_revisi` dan `skor_hitung_ulang` dibuat tetapi tidak dipakai (selalu NULL dan false).
- Halaman daftar batch di Beranda tetap dibuat, karena Pengajar perlu membuka batch miliknya (bukan FR tersendiri).

## 4. Aturan produk

- Lembar jawaban WAJIB mencantumkan nomor soal. Sistem memisahkan jawaban per soal berdasarkan nomor itu.
- Satu soal punya satu kunci berupa teks yang diketik. Tidak ada unggah file kunci.
- Nomor soal dibuat sistem berurutan (1, 2, 3, dst). Tampilan per soal berjudul "Soal 1", "Soal 2".
- Maksimal 20 soal per batch. Soal ke-21 ditolak.
- Soal TIDAK BOLEH ditambah setelah ada Lembar Jawaban pertama di batch itu (karena soal tidak bisa diubah atau dihapus, dan jawaban lama tidak akan punya hasil untuk soal baru). Pesan: "Soal tidak dapat ditambah setelah jawaban diunggah."
- Format file jawaban: PDF, PNG, JPG/JPEG. Maksimal 10 MB per file. PDF maksimal 15 halaman. Validasi berdasarkan isi file (signature byte), bukan hanya ekstensi.
- Unggahan bersifat all-or-nothing: jika satu file atau satu nama tidak valid, TOLAK seluruh unggahan, simpan apa pun tidak, dan tampilkan alasannya.
- Nama peserta didik diisi per file, tidak boleh kosong (setelah trim). Nama yang sama boleh dipakai berulang.
- Maksimal 10 file per unggahan. Tidak ada batas jumlah total file per batch di prototipe (FR19 tidak diterapkan). Backend tetap memecah file ke grup maksimal 5 file per request OCR (bagian 8).
- Data tidak dapat diubah atau dihapus satuan di prototipe: kunci jawaban, file jawaban, nama peserta didik. Kesalahan input diperbaiki dengan membuat batch baru.
- Isolasi data: Pengajar hanya dapat mengakses batch miliknya. Akses ke ID milik Pengajar lain atau ID yang tidak ada mengembalikan 404.
- Nilai akhir dan edit teks OCR tidak ada di prototipe (Cadangan).
- Privasi: pada Gemini free tier, konten yang dikirim dapat dipakai Google untuk peningkatan produk dan dibaca reviewer manusia. Cantumkan sebagai catatan di README, jangan di UI.

## 5. Data

PostgreSQL 15+, SQLAlchemy 2.0 async, migrasi hanya lewat Alembic. Semua PK adalah UUID. Pola nama PK `id_<tabel>`, kecuali `File_Jawaban` (`id_file`) dan `Hasil_Koreksi` (`id_koreksi`). Nama tabel dan kolom di bawah adalah nama persis di kode dan database, dan tabel ini adalah satu-satunya sumber skema. Jika sebuah nama kolom tidak tertulis di sini, tanya.

Enum PostgreSQL native. Di SQLAlchemy pakai Python `Enum` dengan `values_callable` agar yang tersimpan adalah nilai huruf kecil seperti `free`, bukan `FREE`.

| Tabel | Kolom |
|---|---|
| `Pengguna` | `id_pengguna`, `nama` VARCHAR(100) NOT NULL, `email` VARCHAR(255) UNIQUE NOT NULL (disimpan lowercase), `password_hash` VARCHAR(255) NOT NULL (bcrypt), `status_langganan` ENUM('free','pro') NOT NULL DEFAULT 'free' (tidak dipakai), `masa_berlaku_pro` TIMESTAMP NULL (tidak dipakai), `dibuat_pada` TIMESTAMP NOT NULL DEFAULT now() |
| `Sesi` | `id_sesi`, `id_pengguna` FK NOT NULL ON DELETE CASCADE, `refresh_token_hash` VARCHAR(64) UNIQUE NOT NULL (SHA-256), `dibuat_pada` NOT NULL DEFAULT now(), `terakhir_dipakai_pada` NOT NULL (diisi service), `kedaluwarsa_pada` NOT NULL (diisi service), `dicabut_pada` NULL |
| `Batch` | `id_batch`, `id_pengguna` FK NOT NULL ON DELETE CASCADE, `nama_batch` VARCHAR(100) NOT NULL, `status` ENUM('aktif','selesai') NOT NULL DEFAULT 'aktif', `dibuat_pada` NOT NULL DEFAULT now() |
| `Soal` | `id_soal`, `id_batch` FK NOT NULL ON DELETE CASCADE, `no_soal` INT NOT NULL, `kunci_jawaban` TEXT NOT NULL. UNIQUE (`id_batch`, `no_soal`). Tanpa teks soal, tanpa vektor |
| `File_Jawaban` | `id_file`, `id_batch` FK NOT NULL ON DELETE CASCADE, `nama_peserta_didik` VARCHAR(100) NOT NULL, `path` VARCHAR(255) NOT NULL, `status_proses` ENUM('diproses','selesai','gagal') NOT NULL, `pesan_error` TEXT NULL, `jumlah_retry` INT NOT NULL DEFAULT 0, `diunggah_pada` TIMESTAMP NOT NULL DEFAULT now() |
| `Hasil_Koreksi` | PK `id_koreksi`, `id_file` FK NOT NULL ON DELETE CASCADE, `id_soal` FK NOT NULL ON DELETE CASCADE, `teks_ocr` TEXT NOT NULL DEFAULT '', `skor_sistem` INT NULL (CHECK 0 sampai 100), `kategori` ENUM('sangat_mirip','cukup_mirip','kurang_mirip') NULL, `skor_revisi` INT NULL (tidak dipakai), `skor_hitung_ulang` BOOLEAN NOT NULL DEFAULT false (tidak dipakai). UNIQUE (`id_file`, `id_soal`). Tanpa kolom `alasan`, tanpa vektor |

Aturan data:
- `File_Jawaban.path` adalah path relatif `uploads/<id_batch>/<id_file>.<ext>` di bawah direktori unggahan dari environment variable `UPLOAD_DIR`. Nama asli file TIDAK disimpan.
- `kategori` NULL selama `skor_sistem` NULL. Kategori dihitung dari `skor_sistem` oleh satu fungsi (bagian 7), tidak ditulis di tempat lain.
- `jumlah_retry` menghitung retry manual saja (Cadangan). Retry otomatis tidak dihitung.
- Penghapusan Batch (Cadangan) menghapus berkas fisik oleh backend dan baris turunan lewat cascade.

## 6. Autentikasi dan sesi

Dikunci di SRS 2.5. Implementasi manual.

- Endpoint (prefix `/api/auth`): `POST /daftar` (201, `{nama, email, password}` → `{id_pengguna, nama, email}`); `POST /masuk` (200, `{email, password}` → `{access_token}` + cookie `refresh_token`); `POST /refresh` (200, baca cookie `refresh_token` → `{access_token}` + cookie `refresh_token` diperbarui); `POST /keluar` (204, baca cookie `refresh_token` → tanpa isi, cookie dihapus); `GET /saya` (200, header `Authorization: Bearer <access_token>` → `{nama}`).
- Registrasi: `nama`, `email`, `password`. Email di-trim dan di-lowercase. Password minimal 8 karakter, disimpan sebagai hash bcrypt. Email yang sudah terdaftar ditolak dengan pesan "Email sudah terdaftar". Setelah sukses, arahkan ke halaman masuk dengan pesan "Akun berhasil dibuat, silakan masuk". Registrasi tidak membuat sesi.
- Login: `email` dan `password`. Jika gagal, pesan generik "Email atau password salah" (tanpa membedakan email atau password). Jika sukses, buat satu baris `Sesi` dan kirim access token.
- Access token: JWT (HS256, rahasia `SECRET_KEY` dari environment), berlaku 15 menit, berisi `id_pengguna`, `id_sesi`, `exp`. Frontend menyimpannya di memori saja (bukan localStorage).
- Refresh token: string acak (`secrets.token_urlsafe`), BUKAN JWT. Yang disimpan di `Sesi.refresh_token_hash` hanya hash SHA-256-nya. Dikirim lewat cookie `refresh_token`: httpOnly, SameSite=Lax, Path=/api/auth, masa 7 hari. Flag Secure dikendalikan environment variable `COOKIE_SECURE` (false di localhost http).
- Refresh: endpoint membaca cookie, cari `Sesi` dengan hash itu, `dicabut_pada` NULL, `kedaluwarsa_pada` belum lewat. Jika valid, set `terakhir_dipakai_pada` dan `kedaluwarsa_pada` menjadi sekarang + 7 hari (sliding), dan terbitkan access token baru. Refresh token TIDAK dirotasi. Jika tidak valid, 401.
- Setiap request ke endpoint terproteksi: verifikasi JWT, lalu cek di database bahwa `Sesi` itu belum dicabut dan belum kedaluwarsa, lalu baca `Pengguna`. Sesi yang dicabut langsung tidak berlaku.
- Logout: mengisi `dicabut_pada` pada sesi perangkat itu dan menghapus cookie. Tidak ada menu "keluar dari semua perangkat".
- Frontend: saat aplikasi dibuka (termasuk reload), panggil endpoint refresh untuk memulihkan sesi. Jika access token habis atau menerima 401 pada request, panggil refresh sekali (single-flight: request paralel menunggu satu panggilan refresh yang sama), lalu ulangi request. Jika refresh gagal, arahkan ke halaman masuk.
- Semua halaman dan endpoint kecuali registrasi, login, dan refresh membutuhkan login.
- Rate limit login dan reset password TIDAK diterapkan di prototipe.

## 7. Penilaian (LLM-judge)

Keputusan 17 Okt 2026: penentu skor adalah LLM-judge `gemini-3.5-flash-lite`. Embedding dan cosine similarity sudah diuji di Spike dan gagal membedakan jawaban salah (0 dari 21 terdeteksi), sehingga TIDAK dipakai. Jangan menulis kode embedding.

- Input: pasangan (kunci jawaban, teks jawaban hasil OCR) untuk semua item dalam satu grup file, dikirim dalam SATU request dengan structured output.
- Output terstruktur per item: id item yang dikembalikan apa adanya dan `skor` (integer 0 sampai 100). Tanpa alasan.
- Skala berjangkar yang HARUS ada di prompt: 0 untuk salah; 1 sampai 39 sebagian kecil benar; 40 sampai 79 sebagian benar; 80 sampai 100 benar. Penilaian atas kebenaran isi, bukan gaya penulisan, ejaan, atau kesalahan baca OCR yang kecil.
- Jika teks jawaban kosong (jawaban untuk nomor itu tidak ditemukan), judge TIDAK dipanggil untuk item itu: `skor_sistem` = 0, `kategori` = `kurang_mirip`, `teks_ocr` = ''. UI menampilkan "(jawaban tidak ditemukan)".
- Kategori dari satu fungsi `kategori_dari_skor(skor)`: skor >= 80 `sangat_mirip` (Sangat Mirip), 40 sampai 79 `cukup_mirip` (Cukup Mirip), < 40 `kurang_mirip` (Kurang Mirip). Konstanta ini tetap dan tidak bisa diubah Pengajar.
- Skor adalah pendapat model dan dapat bervariasi antar run. Ditampilkan sebagai rekomendasi.
- Hasil Spike untuk acuan: jawaban benar mendapat skor 95 ke atas, jawaban salah 0, jawaban sebagian tersebar luas (sekitar 20 sampai 100) dan paling rawan meleset.
- Skor untuk soal berbentuk poin dihitung atas seluruh teks jawaban, bukan per poin.

## 8. Pemrosesan

- Berjalan async dengan FastAPI `BackgroundTasks`, satu worker, tanpa Celery atau Redis. Background task membuat session database sendiri.
- Setelah unggahan lolos validasi dan tersimpan, semua file berstatus `diproses` dan pemrosesan dimulai. Respons unggahan tidak menunggu pemrosesan.
- Pengelompokan: file dibagi ke grup menurut urutan unggah. Satu grup berisi maksimal 5 file, total 15 MB, dan total 15 halaman (gambar dihitung 1 halaman). Satu file selalu muat dalam satu grup.
- Per grup, dua panggilan Gemini berurutan:
  1. OCR: satu request berisi semua file dalam grup dan daftar nomor soal batch itu. Output terstruktur per file: daftar `{no_soal, teks}`. Hanya nomor soal yang ada di batch. Jika jawaban untuk suatu nomor tidak ditemukan, JANGAN dimasukkan (kosong). Model TIDAK BOLEH menebak nomor soal, termasuk pada lembar tanpa nomor (Spike: Flash-Lite menebak jika lembar tanpa nomor).
  2. Judge (bagian 7): satu request untuk semua item (file x soal) dalam grup.
- Lalu simpan `Hasil_Koreksi` untuk setiap pasangan (file, soal batch itu), idempotent (unik per file dan soal), dan ubah status file menjadi `selesai`.
- Maksimal 2 panggilan Gemini paralel (semaphore). Panggilan lain menunggu.
- Semua panggilan Gemini HARUS lewat satu modul layanan (`backend/app/services/gemini.py`). Tidak ada file lain yang mengimpor `google-genai`. Modul itu memuat fungsi OCR grup, fungsi judge grup, retry, semaphore, dan penghitung anggaran.
- Penghitung anggaran: menghitung jumlah panggilan per model per hari (hari mengikuti zona waktu America/Los_Angeles, sama dengan reset kuota Google), disimpan di memori proses (hilang saat restart, diterima untuk prototipe). Batas dari environment variable `GEMINI_RPD_LIMIT` (default 450, di bawah batas 500). Jika batas tercapai, panggilan tidak dikirim dan diperlakukan sebagai kuota harian habis (tanpa retry). Setiap panggilan dicatat di log: model, jumlah item, dan hitungan harian, tanpa isi file, teks, atau kunci.
- Retry otomatis per grup: maksimal 3 kali dengan jeda 10, 30, 60 detik, hanya untuk 429 per menit dan kegagalan sementara (503, timeout). TIDAK ada retry jika kuota harian (RPD) habis. Jika kegagalan tidak dapat dibedakan dari kuota harian, perlakukan sebagai kuota harian (tanpa retry).
- Jika sebuah grup gagal permanen: semua file di grup itu menjadi `gagal` dengan `pesan_error`, grup lain tidak terpengaruh. Jika OCR sudah berhasil tetapi judge gagal, simpan `teks_ocr` dengan `skor_sistem` NULL, file tetap `gagal`.
- Pesan `pesan_error` ditulis dalam Bahasa Indonesia, tanpa detail teknis atau kunci. Untuk 429, kuota, dan 503: "Layanan AI sedang sibuk atau kuota harian habis, coba lagi nanti." Untuk lainnya: "Gagal membaca file, silakan coba lagi."
- Saat server start, semua file berstatus `diproses` diubah menjadi `gagal` dengan pesan "Pemrosesan terhenti karena server dimulai ulang."
- Hemat API: panggilan dibatch seperti di atas, hasil disimpan sehingga tidak dihitung ulang tanpa alasan, API key hanya dari `GEMINI_API_KEY`. Semua test memakai mock Gemini.
- Frontend polling status tiap 5 detik, hanya selama ada file `diproses` pada batch yang sedang dibuka.

## 9. Layar dan alur

Halaman: Masuk, Daftar, Beranda, Halaman Batch. Halaman Batch punya tiga tab: Soal dan Jawaban, Status Pemrosesan, tabel Dashboard Hasil Koreksi. Semua teks UI Bahasa Indonesia.

### F-AUTH (FR1 tanpa reset)
Mengikuti bagian 6. Beranda hanya dapat diakses setelah login. Tombol Keluar tersedia di semua halaman terproteksi.

### F-BATCH (FR3, UC-02)
1. Di Beranda, Pengajar melihat daftar batch miliknya (nama, tanggal dibuat) dan tombol "Buat Batch Baru".
2. Form meminta nama batch. Pengajar menekan "Buat".
3. Sistem memvalidasi nama tidak kosong (setelah trim), membuat batch berstatus `aktif`, lalu membuka Halaman Batch yang baru.
- Nama kosong: tampilkan pesan validasi, tidak menyimpan.
- Gagal simpan: "Gagal membuat batch, silakan coba lagi", batch tidak dibuat.

### F-KUNCI (FR4, UC-04, hanya ketik)
Di tab Soal dan Jawaban:
1. Pengajar menekan "Tambah Soal". Sistem menyiapkan "Soal N" berikutnya dengan satu kolom teks kunci jawaban.
2. Pengajar mengetik kunci dan menekan "Simpan Kunci Jawaban".
3. Sistem memvalidasi tidak kosong, menyimpan, dan menampilkan konfirmasi serta menambahkan soal ke daftar. Daftar soal menampilkan nomor dan kunci jawaban (hanya baca).
- Kunci kosong: "Kunci jawaban tidak boleh kosong", tidak menyimpan.
- Soal ke-21, atau penambahan setelah ada lembar jawaban: ditolak sesuai bagian 4.
- Gagal simpan: tampilkan pesan error, soal tidak ditambahkan, Pengajar boleh menekan Simpan lagi.

### F-UNGGAH (FR8, FR9, UC-05)
Prasyarat: batch memiliki minimal satu soal. Di tab Soal dan Jawaban:
1. Pengajar menekan "Upload Jawaban Peserta Didik" dan memilih satu sampai 10 file.
2. Sistem menampilkan daftar file terpilih, tiap file dengan kolom nama peserta didik yang masih kosong.
3. Pengajar mengisi nama untuk tiap file lalu menekan "Upload".
4. Sistem memvalidasi semua nama terisi dan semua file valid (bagian 4). Jika ada yang tidak valid, tolak seluruh unggahan tanpa menyimpan apa pun dan tampilkan alasannya; daftar file tetap tampil.
5. Sistem menyimpan file dan nama, mengelompokkan, memulai pemrosesan (bagian 8), dan menampilkan status "Diproses".
- Nama kosong: "Nama peserta didik wajib untuk semua file".
- Lebih dari 10 file: "Maksimal 10 file per unggahan."
- Belum ada soal: "Tambahkan minimal satu soal sebelum mengunggah jawaban."
- Gagal simpan: tampilkan pesan error dan tidak ada file tersimpan (hapus berkas yang sempat tertulis). Pengajar dapat mengunggah ulang.

### F-STATUS (FR11 bagian tampilan, UC-06)
Tab Status Pemrosesan:
1. Sistem menampilkan daftar semua file jawaban batch itu: nama peserta didik, status (Diproses, Selesai, Gagal), dan `pesan_error` untuk yang Gagal.
2. Selama ada file Diproses, daftar diperbarui tiap 5 detik.
- Gagal memuat: "Gagal memuat status pemrosesan, coba muat ulang halaman", daftar tidak ditampilkan.
- Tombol "Coba Lagi" adalah Cadangan dan tidak dibuat.

### F-DASHBOARD (FR12, FR13, FR14, FR15, UC-07)
Tab tabel Dashboard Hasil Koreksi:
1. Sistem menampilkan pilihan soal ("Soal 1", "Soal 2", dst). Soal pertama terpilih awal.
2. Untuk soal terpilih, tabel dengan satu baris per peserta didik yang file-nya berstatus Selesai. Kolom: Peserta Didik, Teks OCR, Skor Kemiripan (0 sampai 100), Kategori Kualitatif (teks, bukan hanya warna). Teks OCR yang panjang boleh dipotong dengan opsi menampilkan lengkap.
3. Jika Pengajar memilih soal lain, tabel diganti sesuai soal itu.
- Belum ada file Selesai: "Belum ada hasil koreksi untuk soal ini. Tunggu proses selesai."
- Gagal memuat: "Koneksi internet terputus, coba muat ulang halaman."
- Tidak ada kolom alasan, tidak ada pratinjau gambar asli, tidak ada nilai huruf.

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

## 11. Lingkungan localhost

- Database: PostgreSQL lewat Docker Compose. Backend dan frontend dijalankan langsung di mesin pengembang.
- Backend di port 8000. Frontend (Vite) di port 5173 dengan proxy `/api` ke backend, sehingga browser hanya melihat satu origin (cookie httpOnly bekerja tanpa CORS khusus).
- Environment variable (dibuat di `.env`, contoh tanpa nilai di `.env.example`): `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, `UPLOAD_DIR`, `COOKIE_SECURE`.
- Direktori unggahan dan `.env` masuk `.gitignore`.
- Perintah menjalankan ditulis di README dan CLAUDE.md setelah kerangka aplikasi ada.

## 12. Persyaratan non-fungsional untuk prototipe

- Password di-hash (bcrypt). Rahasia hanya dari environment variable.
- Isolasi data antar Pengajar (bagian 4).
- Operasi non-AI (login, daftar batch, tabel Dashboard) merespons dalam 5 detik pada kondisi normal.
- OCR satu file (sampai 10 MB) selesai dalam 1 menit. Satu batch 15 file selesai dalam 25 menit.
- Pesan error jelas dan berbahasa Indonesia. Indikator loading tampil pada unggah, pemrosesan, dan pemuatan data.
- Layout responsif, dioptimalkan untuk desktop.
- Data yang sudah berhasil diproses tetap tersimpan walau sebagian file gagal.
- Tampilan mengikuti `docs/UI.md` (Tailwind CSS, token warna dari logo, logo, kontras). Tanpa warna hardcode di komponen.

## 13. Undecided

Item di sini TIDAK BOLEH diimplementasikan berdasarkan asumsi. Angkat saat Plan mode.

| # | Hal | Keterangan |
|---|---|---|
| U1 | Nama PK `Hasil_Koreksi` | Diputuskan: mengikuti ERD final (`id_koreksi`) |
| U2 | Pratinjau gambar asli di tabel Dashboard Hasil Koreksi | Tidak ada di prototipe |
| U3 | Ambang kategori ≥80 / 40–79 / <40 | Diusulkan dari hasil Spike, berlaku sampai SRS direvisi |

## 14. Changelog

| Tanggal | Perubahan |
|---|---|
| 2026-10-17 | Draf awal |
| 2026-10-17 | Maks 10 file per unggahan. Satu modul layanan Gemini dengan penghitung anggaran. Tailwind dan `docs/UI.md`. Tanpa `docs/ERD.md` |
| 2026-10-17 | Revisi: selaras SRS 38 hlm. 24 FR sebagai penyebut, 10 FR dihitung. Nama kode mengikuti ERD Indonesia. Sesi lengkap (tabel `Sesi`). Tanpa kolom alasan. Kategori Sangat/Cukup/Kurang Mirip. Kunci hanya diketik. Soal tidak dapat ditambah setelah ada jawaban |
| 2026-10-18 | Selaraskan nama dengan ERD final (SDD): `Batch.nama` → `nama_batch`; `Soal.nomor_soal` → `no_soal`; `File_Jawaban.id_file_jawaban` → `id_file`; `File_Jawaban.status_pemrosesan` → `status_proses`; tambah `File_Jawaban.diunggah_pada`; `Hasil_Koreksi.id_hasil_koreksi` → `id_koreksi`; `Hasil_Koreksi.id_file_jawaban` → `id_file`; `Hasil_Koreksi.skor_perlu_dihitung_ulang` → `skor_hitung_ulang`. U1 diputuskan |
| 2026-10-18 | Lengkapi SPEC bagian 5 dari ERD final (celah untuk K-01): panjang VARCHAR (`Pengguna.nama` 100, `Pengguna.email` 255, `Pengguna.password_hash` 255, `Batch.nama_batch` 100, `File_Jawaban.nama_peserta_didik` 100, `File_Jawaban.path` 255); semua FK (`id_pengguna`, `id_batch`, `id_soal`, `id_file`) NOT NULL; `Sesi.dibuat_pada` DEFAULT now(), `Sesi.terakhir_dipakai_pada`/`kedaluwarsa_pada` NOT NULL tanpa default; `Batch.dibuat_pada` NOT NULL DEFAULT now() |
| 2026-10-18 | Tugas A1a (autentikasi backend): catat path endpoint `/api/auth/{daftar,masuk,refresh,keluar,saya}` di bagian 6; tambah tabel kode error autentikasi (`VALIDASI_GAGAL`, `EMAIL_SUDAH_TERDAFTAR`, `PASSWORD_TERLALU_PENDEK`, `PASSWORD_TERLALU_PANJANG`, `LOGIN_GAGAL`, `SESI_BERAKHIR`) di bagian 10 |