# Koreksi-in

Web app autograding jawaban esai/jawaban singkat berbasis semantic similarity (OCR + AI embedding), dengan sistem langganan berbayar.

Status: prototipe UTS, hanya dijalankan di localhost. Lihat `docs/SPEC.md` untuk kebutuhan dan `CLAUDE.md` untuk aturan kerja.

## Menjalankan di localhost

1. Salin `.env.example` menjadi `.env` di root proyek dan isi semua nilainya (`DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GEMINI_RPD_LIMIT`, `UPLOAD_DIR`, `COOKIE_SECURE`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). `DATABASE_URL` harus memakai driver `asyncpg`, contoh bentuk: `postgresql+asyncpg://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:5432/<POSTGRES_DB>`.
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
6. Cek: `curl http://localhost:8000/api/health` harus mengembalikan `{"status":"ok"}`.

Frontend belum dibuat di tahap ini.

## Lint, format, test (backend)

Dari folder `backend/` dengan virtualenv aktif:

- Lint: `ruff check .`
- Format: `ruff format .`
- Test: `pytest`

## Catatan privasi Gemini

Prototipe ini memakai Gemini free tier (`gemini-3.5-flash-lite`) untuk OCR dan penilaian. Pada tingkat free tier, konten yang dikirim ke Gemini dapat dipakai Google untuk peningkatan produk dan dapat dibaca oleh reviewer manusia. Jangan mengunggah data sensitif atau rahasia melalui prototipe ini.
