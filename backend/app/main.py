from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="Koreksi-in")

app.include_router(health.router, prefix="/api")
