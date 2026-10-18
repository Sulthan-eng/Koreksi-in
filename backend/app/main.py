from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.database import AsyncSessionLocal
from app.core.errors import AppError, app_error_handler, validation_error_handler
from app.core.startup import sapu_proses_tergantung
from app.routers import auth, batch, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await sapu_proses_tergantung(db)
    yield


app = FastAPI(title="Koreksi-in", lifespan=lifespan)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
