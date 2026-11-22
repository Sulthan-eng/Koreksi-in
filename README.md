# Koreksi-in

Web app autograding jawaban esai/jawaban singkat. OCR mengekstrak teks jawaban peserta didik, lalu LLM-judge (Gemini) memberi skor kemiripan sebagai rekomendasi bagi Pengajar. Dilengkapi sistem langganan berbayar.

Status: dikembangkan bertahap menuju sistem penuh. Saat ini dijalankan di localhost; sistem di-deploy ke Fly.io (backend, `https://api.sulthanfarizan.my.id`), Supabase (Postgres dan penyimpanan berkas), dan Netlify (frontend, `https://app.sulthanfarizan.my.id`) — sisa detail deploy (rotasi rahasia produksi, backup) belum diputuskan, lihat `docs/SPEC.md` U13. Lihat `docs/SPEC.md` untuk kebutuhan dan status tiap fitur (bagian 3), dan `CLAUDE.md` untuk aturan kerja.

## Menjalankan di localhost

1. Salin `.env.example` menjadi `.env` di root proyek dan isi semua nilainya (`DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, `UPLOAD_DIR`, `STORAGE_BACKEND`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `COOKIE_SECURE`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FRONTEND_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). Lima variabel terkait SMTP dan `FRONTEND_URL` dipakai untuk reset password (SPEC bagian 11) dan semuanya sudah punya default, sehingga server dan test tetap berjalan tanpa mengisinya; bila `SMTP_USER` atau `SMTP_PASSWORD` kosong, email reset password tidak dikirim. `DATABASE_URL` harus memakai driver `asyncpg`, contoh bentuk: `postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:5432/<POSTGRES_DB>`. `STORAGE_BACKEND` (default `lokal`) memilih lapisan penyimpanan berkas jawaban (SPEC bagian 11): untuk localhost biarkan `lokal` dan isi `UPLOAD_DIR`; kelima variabel `S3_*` hanya wajib bila `STORAGE_BACKEND=s3` (produksi, Supabase Storage) dan boleh dikosongkan untuk pengembangan lokal. Pengaturan pool koneksi database `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE_SECONDS` (SPEC bagian 11) semuanya opsional dengan default yang masuk akal untuk satu instance, sehingga tidak ada di `.env.example` dan tidak perlu diisi kecuali ingin menyesuaikan batas koneksi pooler database.
2. Jalankan database: `docker compose up -d db`.
3. Siapkan backend:
   ```
   cd backend
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```
4. Terapkan migrasi: `alembic upgrade head`.
5. Jalankan backend: `uvicorn app.main:app --reload --port 8000`.
   Catatan: `ENV` ber-default `produksi` (gagal-aman), sehingga `/docs`, `/redoc`, dan `/openapi.json` nonaktif secara default. Jika memerlukan Swagger/OpenAPI di localhost, jalankan `ENV=dev uvicorn app.main:app --reload --port 8000` atau tambahkan `ENV=dev` di `.env` lokal (`ENV` sengaja tidak dimasukkan ke `.env.example`).
6. Cek: `curl http://localhost:8000/api/health` harus mengembalikan `{"status":"ok"}`.

7. Siapkan frontend (butuh Node 20.19+ atau 22.12+):
   ```
   cd frontend
   npm install
   ```
   Opsional: salin `frontend/.env.example` menjadi `frontend/.env` dan isi `VITE_API_URL` bila backend tidak berada di origin yang sama (lihat `docs/SPEC.md` bagian 11). Dikosongkan atau tidak dibuat sama sekali berarti path relatif lewat proxy Vite di bawah, yaitu alur localhost yang biasa.
8. Jalankan frontend: `npm run dev` (port 5173, proxy `/api` ke backend di port 8000).
9. Buka `http://localhost:5173`.

Fitur yang sudah berjalan dan yang belum dikerjakan tercantum di `docs/SPEC.md` bagian 3.

## Menjalankan backend lewat Docker (opsional)

Berguna untuk menguji image yang sama dengan yang dipakai di produksi. Alur pengembangan sehari-hari tetap memakai `uvicorn --reload` seperti di atas. Semua perintah dari root proyek, dan port 8000 harus bebas lebih dulu.

Compose meng-override `DATABASE_URL` ke host `db` (bukan `localhost`) dan memaksa `STORAGE_BACKEND=lokal` dengan volume untuk `UPLOAD_DIR`, jadi Supabase dan S3 tidak tersentuh. `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, dan ketiga variabel `POSTGRES_*` tetap dibaca dari `.env` di root.

1. Bangun image: `docker compose build backend`.
2. Jalankan database: `docker compose up -d db` (tunggu `docker compose ps` menunjukkan `db` `healthy`).
3. Terapkan migrasi: `docker compose run --rm backend alembic upgrade head`. Langkah ini terpisah dan harus dijalankan sebelum backend start, karena saat boot backend menyapu file yang berstatus `diproses` dan membutuhkan tabelnya sudah ada.
4. Jalankan backend: `docker compose up -d backend`.
5. Cek: `curl http://localhost:8000/api/health` harus mengembalikan `{"status":"ok"}`.
6. Hentikan: `docker compose down` (tanpa `-v`, agar data database dan unggahan dev tidak terhapus).

## Deploy backend ke Fly.io

Semua perintah dari folder `backend/` (di situlah `fly.toml` berada, sehingga build context Fly sama dengan build context Compose).

1. `fly launch --no-deploy --copy-config` — **tolak** tawaran Postgres, Redis, dan Tigris; database dan penyimpanan berkas dipakai dari Supabase.
2. `fly config validate` — periksa `fly.toml` sebelum deploy.
3. Isi variabel dengan `fly secrets set <NAMA>=<nilai>`. Nama yang perlu diisi: `DATABASE_URL` (harus berawalan `postgresql+asyncpg://` dan memakai connection string **Session pooler** Supabase), `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, `STORAGE_BACKEND` (bernilai `s3`), `S3_ENDPOINT_URL`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `COOKIE_SECURE` (bernilai `true`), `FRONTEND_URL` (bernilai `https://app.sulthanfarizan.my.id`), `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`. Opsional, dengan default aman (lihat `docs/SPEC.md` bagian 11): `ENV` (isi `produksi` untuk kejelasan meski itu defaultnya — default gagal-aman dipilih justru supaya lupa mengisinya tidak membuka origin dev maupun `/docs`/`/redoc`/`/openapi.json`), `COOKIE_SAMESITE`, `MAX_REQUEST_SIZE_MB`. Siapkan custom domain `api.sulthanfarizan.my.id` lewat `fly certs add api.sulthanfarizan.my.id` dan arahkan DNS sesuai instruksi `fly certs show`.
4. `fly deploy --ha=false` — **`--ha=false` wajib**: tanpa itu deploy pertama membuat dua mesin, dan itu merusak asumsi satu instance/satu worker (penghitung kuota Gemini ada di memori dan pemrosesan memakai `BackgroundTasks`). Migrasi dijalankan lebih dulu oleh `release_command` (`alembic upgrade head`).
5. `fly status` — pastikan hanya ada satu mesin. Bila ternyata lebih dari satu, perbaiki dengan `fly scale count 1`.
6. Cek: `curl https://<nama-app>.fly.dev/api/health` harus mengembalikan `{"status":"ok"}`, dan `/docs` mengembalikan `404`. `fly logs` memuat log aplikasi `app.*` mulai level `INFO` (termasuk `storage_backend_aktif backend=s3` dan `gemini_call`).

Catatan penting:

- **Jangan mengisi variabel dengan nilai kosong.** `fly secrets set NAMA=` tetap mengirim variabel itu ke proses dan menimpa default di `Settings`. String kosong pada variabel bertipe angka (`GEMINI_RPD_LIMIT`, `SMTP_PORT`) atau pilihan terbatas (`STORAGE_BACKEND`, `COOKIE_SECURE`) menggagalkan validasi saat import, sehingga aplikasi dan `release_command` langsung mati. Variabel opsional cukup tidak di-set.
- **`UPLOAD_DIR` tidak diisi di produksi.** `STORAGE_BACKEND=s3` tidak memakainya, dan container stateless (tanpa Fly Volume).
- `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE_SECONDS` opsional; defaultnya sudah sesuai untuk satu instance.
- Mesin tidur saat idle dan bangun otomatis saat ada request (`auto_stop_machines = "stop"`, `min_machines_running = 0`) untuk menghemat biaya selama tidak ada demo. Konsekuensinya, pemrosesan berjalan sebagai `BackgroundTasks` di dalam proses aplikasi: bila tidak ada lalu lintas (misalnya tab ditutup saat proses berjalan), mesin bisa berhenti dan pemrosesan terputus. File yang terputus ditandai `Gagal` saat boot berikutnya dan bisa dikirim ulang lewat "Coba Lagi" (SPEC bagian 8). Sebelum demo atau penilaian, kembalikan ke `auto_stop_machines = "off"` dan `min_machines_running = 1`.
- Deploy mematikan satu-satunya mesin, jadi file yang sedang `diproses` akan ditandai `Gagal` dengan pesan "server dimulai ulang". Hindari deploy saat ada pemrosesan berjalan.

## Deploy frontend ke Netlify

Konfigurasi ada di `frontend/netlify.toml` (base directory `frontend`, build `npm run build`, publish `dist`, redirect SPA ke `index.html`). Tanpa proxy `/api`: timeout fungsi Netlify terlalu pendek untuk `ocr-kunci`, jadi frontend memanggil API langsung lewat origin lain.

1. Hubungkan repositori ke Netlify, dengan base directory `frontend`.
2. Isi environment variable di dashboard Netlify (bukan di `netlify.toml`, supaya alamat API tidak tertanam di repositori): `VITE_API_URL=https://api.sulthanfarizan.my.id`. Ingat variabel `VITE_*` ditanam saat build dan terlihat publik di JS yang terkirim ke browser — jangan menaruh rahasia di sana.
3. Deploy. Netlify menerbitkan di domain `*.netlify.app`; tambahkan custom domain `app.sulthanfarizan.my.id` lewat menu Domain settings dan arahkan DNS sesuai instruksi Netlify. HTTPS otomatis terkelola Netlify.
4. Cek: buka `https://app.sulthanfarizan.my.id`, masuk, dan pastikan tidak ada galat CORS di console browser. Backend harus sudah mengisi `FRONTEND_URL=https://app.sulthanfarizan.my.id` (lihat bagian Fly.io di atas) agar origin ini diizinkan.

## Lint, format, test (backend)

Dari folder `backend/` dengan virtualenv aktif:

- Lint: `ruff check .`
- Format: `ruff format .`
- Test: `pytest`

## Lint, format (frontend)

Dari folder `frontend/`:

- Lint: `npm run lint`
- Format: `npm run format`
- Build: `npm run build`

## Catatan privasi Gemini

Aplikasi ini memakai Gemini free tier (`gemini-3.5-flash-lite`) untuk OCR dan penilaian. Pada tingkat free tier, konten yang dikirim ke Gemini dapat dipakai Google untuk peningkatan produk dan dapat dibaca oleh reviewer manusia. Selama masih memakai free tier, jangan mengunggah data sensitif atau rahasia.