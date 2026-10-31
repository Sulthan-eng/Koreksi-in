# Gaya kode Koreksi-in

Konvensi untuk agent. Aturan perilaku ada di `CLAUDE.md`, kebutuhan di `docs/SPEC.md`, tampilan di `docs/UI.md`. Jika dokumen ini tidak menyebut sesuatu, ikuti pola yang sudah ada di kode, jangan membuat pola baru.

Prinsip: sederhana, eksplisit, mudah dibaca orang. Tidak ada abstraksi yang belum dibutuhkan.

## Penamaan

- Konsep domain mengikuti nama ERD Indonesia dari SPEC bagian 5: `Pengguna`, `Batch`, `Soal`, `File_Jawaban`, `Hasil_Koreksi`, `skor_sistem`, `nama_peserta_didik`, dst. Jangan diterjemahkan.
- Kata teknis kerangka kerja berbahasa Inggris: router, service, schema, session, hook, props.
- Python: `snake_case` untuk fungsi dan variabel, `PascalCase` untuk kelas. Kelas model SQLAlchemy memakai nama tabel persis (`Hasil_Koreksi` boleh ditulis `HasilKoreksi` sebagai nama kelas, nama tabel tetap `Hasil_Koreksi`). Konsisten satu cara di seluruh kode.
- JavaScript: `camelCase` untuk fungsi dan variabel, `PascalCase` untuk komponen dan file komponen. Field data dari API dipakai apa adanya (`skor_sistem`), jangan diubah ke camelCase.
- Nama harus menjelaskan isi. Hindari singkatan kecuali yang umum (`id`, `url`, `db`).

## Backend (Python, FastAPI)

Struktur di `backend/app/`:

- `routers/`: endpoint tipis. Hanya validasi masukan, panggil service, bentuk respons. Tidak ada logika bisnis dan tidak ada query langsung.
- `services/`: logika bisnis dan akses database. Satu file per bidang (auth, batch, soal, file_jawaban, pemrosesan, penilaian; saat fiturnya dikerjakan: langganan, pembayaran, ekspor, ringkasan, admin).
- `services/gemini.py`: satu-satunya tempat yang mengimpor `google-genai` (lihat SPEC bagian 8).
- `services/midtrans.py` (saat FR19 dikerjakan): satu-satunya tempat yang memanggil Midtrans dan memvalidasi signature webhook, dengan pola yang sama seperti `gemini.py`.
- `services/email.py` (saat reset password dikerjakan): satu-satunya tempat yang mengirim email (SMTP Gmail), dengan pola yang sama seperti `gemini.py`. Kredensial hanya dari environment variable dan token tidak boleh ditulis ke log.
- `models/`: model SQLAlchemy.
- `schemas/`: skema Pydantic v2 untuk masukan dan keluaran API.
- `core/`: konfigurasi (environment variable), keamanan (hash, JWT), dependensi bersama, penanganan error.

Aturan:

- Semua kode I/O `async`. Tidak ada pemanggilan blocking di dalam fungsi async (untuk hashing bcrypt jalankan di thread).
- Type hint wajib pada fungsi publik.
- Konfigurasi hanya dari environment variable lewat satu objek settings. Tidak ada `os.environ` tersebar.
- Query database lewat SQLAlchemy 2.0 gaya `select()`. Tidak ada SQL mentah kecuali ada alasan yang ditulis di komentar.
- Setiap endpoint terproteksi memakai dependensi `pengguna_saat_ini` yang memverifikasi JWT dan sesi (SPEC bagian 6). Pembatasan peran memakai dependensi turunan (`pengajar_saat_ini` dan `admin_saat_ini`) yang memeriksa `Pengguna.peran` dan `dinonaktifkan_pada` di database pada setiap request; peran TIDAK BOLEH dibaca dari klaim yang dikirim frontend. Setiap query data milik Pengajar menyaring dengan `id_pengguna`. Akses ke data milik orang lain mengembalikan 404.
- Error API: kembalikan kode stabil dalam bentuk `{"kode": "BATCH_TIDAK_DITEMUKAN", "pesan": "..."}`. Frontend memetakan `kode` ke teks Indonesia. `pesan` tidak boleh berisi detail teknis, jejak stack, atau rahasia.
- Validasi file unggahan dilakukan di service, berdasarkan isi file (signature byte), bukan ekstensi.
- Background task membuat session database sendiri, tidak memakai session dari request.
- Log: boleh mencatat id dan hitungan. TIDAK BOLEH mencatat password, token, API key, isi file, atau teks jawaban.
- Format dan lint dengan `ruff`. Test dengan `pytest` dan `pytest-asyncio`, klien uji `httpx`.
- Test: tiap service punya test untuk jalur sukses dan jalur gagal utama. Semua pemanggilan Gemini di-mock, termasuk kegagalan yang tidak bisa dipicu dari luar (satu grup gagal, 503, timeout, retry 10/30/60 detik, kuota harian habis). Test memakai database uji terpisah, bukan database pengembangan. Aturan validasi di SPEC (batas panjang, trim, format email, ukuran 72 byte untuk password) masing-masing punya test pada batas dan di luar batas.
- Komentar hanya untuk menjelaskan alasan, bukan mengulang kode. Docstring singkat pada fungsi service.

## Frontend (React, Vite, JavaScript, Tailwind)

Struktur di `frontend/src/`:

- `pages/`: satu file per halaman sesuai Inventaris halaman di `docs/UI.md` (Pemasaran, Daftar, Masuk, Beranda, HalamanBatch, Langganan, DashboardPantauan, AkunPengajar). File halaman tipis: merangkai komponen dan memegang state halaman, bukan menampung markup panjang.
- `components/`: komponen bersama (daftar di `docs/UI.md`, bagian Komponen bersama: bilah atas, Lencana, dialog konfirmasi, kartu angka, tabel, keadaan data) dan komponen per tab. Satu definisi per komponen; jangan menyalin markup yang sama ke halaman lain.
- `api/`: semua pemanggilan ke backend. Komponen TIDAK memanggil `fetch` langsung.
- `api/klien.js`: satu wrapper `fetch` yang menempelkan access token, menangani 401 dengan satu panggilan refresh bersama (single-flight), dan memetakan `kode` error ke teks Indonesia.
- `index.css`: `@import "tailwindcss"` dan token `@theme` dari `docs/UI.md`.

Aturan:

- Komponen fungsional dan hooks. Tidak ada kelas komponen.
- Access token disimpan di memori modul `api`, tidak di `localStorage` atau `sessionStorage`.
- Saat aplikasi dibuka, panggil endpoint refresh untuk memulihkan sesi sebelum menampilkan halaman terproteksi.
- Polling status 5 detik hanya selama ada file `diproses`, dan harus dibersihkan saat komponen dilepas.
- Setiap data yang dimuat punya tiga keadaan yang ditangani: memuat, kosong, dan gagal (dengan teks dari SPEC).
- Form memakai `noValidate` dan validasi sendiri sehingga pesan tampil dari aplikasi persis seperti di SPEC, bukan bubble bawaan browser.
- Halaman terproteksi dibungkus pelindung rute yang memeriksa login dan peran (Pengajar tidak bisa membuka halaman Admin dan sebaliknya). Pemeriksaan ini hanya kenyamanan UI; yang menentukan adalah backend.
- Peringatan meninggalkan halaman dipasang lewat satu hook bersama dan hanya aktif selama ada data yang belum terkirim (SPEC bagian 9, F-UNGGAH).
- Gaya hanya lewat kelas Tailwind dan token `docs/UI.md`. Jika satu rangkaian kelas dipakai berulang lebih dari tiga kali, ekstrak jadi komponen, bukan `@apply`.
- Teks UI semuanya Bahasa Indonesia. Teks error dan pesan ditaruh di satu berkas pemetaan (`api/pesan.js`), tidak tersebar di komponen.
- Lint dan format dengan `eslint` dan `prettier`.
- Test frontend minimal: fungsi murni (pemetaan kategori ke teks, pemetaan kode error). Tidak ada keharusan test komponen untuk prototipe.

## Git dan dokumen

- Aturan branch, commit, dan PR ada di `CLAUDE.md`.
- Satu PR mengubah satu hal. Jika mengubah perilaku yang tertulis di SPEC, ubah SPEC di PR yang sama dan sebut alasannya di deskripsi PR.
- Perubahan SPEC, UI, atau STYLE yang tidak disertai kode (sinkronisasi dokumen, rancangan halaman baru) dibuat di PR dokumen tersendiri bertipe `docs`.
- Sebelum merombak atau membuat halaman, pastikan halaman itu sudah punya subbagian di `docs/UI.md` bagian Rancangan halaman. Jika belum, tanya pemilik proyek.
- README.md untuk manusia: cara menjalankan di localhost, variabel `.env.example`, dan catatan privasi Gemini. Diisi setelah kerangka aplikasi ada.