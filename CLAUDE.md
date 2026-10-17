# Koreksi-in

Aplikasi web autograding jawaban esai/jawaban singkat. Pengajar (guru atau dosen) memasukkan kunci jawaban dan mengunggah lembar jawaban peserta didik. Sistem mengekstrak teks dengan OCR, lalu LLM-judge memberi skor kemiripan sebagai rekomendasi. Pengajar memegang nilai akhir.

Status: prototipe UTS. Hanya dijalankan di localhost, tidak di-deploy. Kerangka backend dan database (Docker Compose, FastAPI, Alembic) sudah dibuat, tanpa tabel, tanpa autentikasi, tanpa modul Gemini. Kerangka frontend belum dibuat.

Kata HARUS dan TIDAK BOLEH yang ditulis huruf besar berarti aturan wajib.

## Stack

- Backend: Python 3.12, FastAPI (async), PostgreSQL 15+, SQLAlchemy 2.0 async + Alembic + asyncpg
- Frontend: React + Vite (JavaScript) + Tailwind CSS (v4, plugin Vite)
- AI: Google Gemini lewat SDK resmi `google-genai`, model `gemini-3.5-flash-lite` untuk OCR dan judge
- Container: Docker Compose hanya untuk database. Backend dan frontend dijalankan langsung di mesin pengembang.

## Struktur folder

- `backend/`: API FastAPI
- `frontend/`: aplikasi React
- `docs/`: SPEC.md dan dokumen lain
- Skrip Spike ada di branch `tes/spike_model` dan BUKAN bagian aplikasi. Jangan mengimpor atau menyalinnya tanpa diminta.

## Perintah

Semua perintah backend dijalankan dari folder `backend/` dengan virtualenv aktif, kecuali disebut lain.

- Database: `docker compose up -d db` (dari root proyek, butuh `.env` di root berisi `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
- Setup virtualenv: `cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt`.
- Jalankan backend: `uvicorn app.main:app --reload --port 8000`.
- Migrasi: `alembic upgrade head` (terapkan), `alembic current` (lihat revisi aktif).
- Lint: `ruff check .`.
- Format: `ruff format .`.
- Test: `pytest`.

Frontend belum punya perintah karena kerangkanya belum dibuat.

## Workflow

- TIDAK BOLEH bekerja, commit, atau push langsung ke `main`. Sebelum edit pertama, buat branch dari `main` yang mutakhir. Perubahan masuk `main` hanya lewat Pull Request.
- Nama branch: `<type>/<deskripsi-kebab>`, misal `feat/batch-creation`.
- Commit mengikuti Conventional Commits (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`). Satu commit satu perubahan logis.
- Satu PR satu fitur atau satu perhatian. Jika tugas melebar, pecah ke branch dan PR lain.
- Sebelum menyatakan selesai, lint dan test HARUS lolos (setelah perintahnya ada). Sebuah fitur dianggap selesai hanya jika alurnya berjalan ujung ke ujung di localhost tanpa error.
- Perubahan skema database HARUS lewat migrasi Alembic, tidak mengubah tabel manual.
- Agent TIDAK BOLEH mengedit `build/`, `dist/`, `node_modules/`, lockfile secara manual. Ubah manifest lalu jalankan installer.

## Prinsip

- Kerjakan hal paling sederhana yang memenuhi permintaan. Jika terasa perlu menambah sesuatu, tanya dulu, jangan menambah sendiri.
- Fitur di luar `docs/SPEC.md` TIDAK BOLEH ditambahkan. Fitur berstatus "Cadangan" atau "Di luar prototipe" di SPEC bagian 3 TIDAK BOLEH dikerjakan kecuali diminta eksplisit.
- Jika kode dan SPEC bertentangan, atau SPEC diam soal hal yang dibutuhkan: BERHENTI dan tanya. Jangan menebak dan jangan mengubah SPEC agar cocok dengan kode.
- Item di bagian "Undecided" pada SPEC TIDAK BOLEH diimplementasikan berdasarkan asumsi.
- Kejelasan lebih baik daripada kepintaran. Gagal dengan jelas dan cepat, jangan menelan error.
- Database menjaga integritas struktural saja: NOT NULL, UNIQUE, foreign key, enum, CHECK rentang skor.
- Jangan menambah dependensi tanpa alasan yang jelas. Sebutkan alasannya di PR.

## Gemini (aturan hemat API)

Kuota free tier kecil dan dipakai bersama semua pengguna. Aturan ini wajib:

- Semua panggilan Gemini HARUS lewat satu modul layanan (`backend/app/services/gemini.py`) yang memuat retry, semaphore, dan penghitung anggaran per model. Tidak ada file lain yang boleh mengimpor `google-genai`.
- Panggilan Gemini HARUS dibatch: satu request memuat banyak item dengan structured output, bukan satu panggilan per file atau per baris.
- Maksimal 2 panggilan Gemini paralel.
- Jika kuota harian (RPD) habis, JANGAN retry. Tandai file Gagal dengan pesan jelas. Retry (jeda 10, 30, 60 detik) hanya untuk 429 per menit dan kegagalan sementara.
- Simpan hasil agar tidak dihitung ulang tanpa alasan.
- Semua test HARUS memakai mock Gemini. Test TIDAK BOLEH memanggil API sungguhan.
- Agent TIDAK BOLEH menjalankan skrip atau perintah yang memanggil Gemini sungguhan kecuali diminta pemilik proyek.
- API key hanya dari environment variable `GEMINI_API_KEY`.

## Rahasia

- TIDAK BOLEH membaca, mengedit, atau mencetak isi `.env`. Hanya `.env.example` (tanpa nilai) yang boleh dibuat dan di-commit.
- Jangan menaruh API key, token, atau kata sandi di kode, log, atau komit. Jangan menulis token atau kata sandi ke log.
- Direktori unggahan dan `.env` HARUS ada di `.gitignore`.

## Dokumen proyek

- `docs/SPEC.md`: satu-satunya sumber kebutuhan. Agent HARUS membaca bagian yang relevan sebelum merencanakan fitur.
- `docs/UI.md`: palet warna, token Tailwind, logo, dan aturan tampilan. Agent HARUS membacanya sebelum membuat atau mengubah UI.
- `docs/STYLE.md`: konvensi gaya kode backend dan frontend. Agent HARUS membacanya sebelum menulis kode.
- Skema database hanya ada di SPEC bagian 5. Tidak ada file ERD terpisah.
- SRS lengkap (PDF) adalah latar. Bukan bahan baca rutin, dan SPEC menang jika berbeda.
- `README.md`: untuk manusia, bukan sumber kebutuhan.
- Perubahan pada dokumen ini diputuskan di Plan mode dan dibuat dalam PR yang sama dengan kodenya.

## Bahasa dan penamaan

- Teks antarmuka (UI): Bahasa Indonesia. Istilah Inggris TIDAK BOLEH muncul di UI. Pakai "Pengajar", "peserta didik", "Skor Kemiripan", dan "tabel Dashboard Hasil Koreksi" sesuai glosarium SPEC bagian 2.
- Pesan error API ke UI dipetakan dari kode error ke teks Indonesia.
- Identifier untuk konsep domain di kode, database, dan API mengikuti nama ERD Indonesia persis seperti di SPEC bagian 5 (`Pengguna`, `Batch`, `Soal`, `File_Jawaban`, `Hasil_Koreksi`, `skor_sistem`, dst). Kata teknis kerangka kerja (router, service, schema, hook) tetap bahasa Inggris. Jangan menerjemahkan atau mengganti nama kolom ERD.
- Warna di frontend lewat token Tailwind dari `docs/UI.md`, tanpa HEX atau nilai arbitrer seperti `bg-[#123456]` di komponen.
- Commit dan PR: bahasa Inggris, boleh mengutip ID (`UC-05`, `FR8`).