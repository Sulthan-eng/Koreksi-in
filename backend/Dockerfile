# Image backend Koreksi-in. Satu stage: tidak ada dependensi yang perlu dikompilasi
# (pypdf, boto3, google-genai murni Python; asyncpg dan bcrypt punya wheel manylinux),
# sehingga tidak ada paket sistem yang perlu dipasang.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Hanya dependensi runtime: requirements-dev.txt (ruff, pytest) tidak dipasang.
# Dipisah dari COPY kode agar layer dependensi tetap ter-cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# User non-root. /data/uploads hanya dipakai saat STORAGE_BACKEND=lokal (Docker Compose dev);
# di produksi STORAGE_BACKEND=s3 dan direktori ini tetap kosong, container stateless.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /data/uploads \
    && chown -R app:app /data

# alembic.ini dan alembic/ ikut tersalin: dipakai release_command "alembic upgrade head".
COPY --chown=app:app . .

USER app

EXPOSE 8000

# python:3.12-slim tidak memuat curl, jadi probe memakai Python yang sudah ada.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

# Satu worker wajib: penghitung kuota Gemini ada di memori dan pemrosesan memakai
# BackgroundTasks dalam proses yang sama (SPEC U13). --forwarded-allow-ips=* aman karena
# port ini hanya dijangkau proxy Fly (produksi) atau loopback (compose).
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
