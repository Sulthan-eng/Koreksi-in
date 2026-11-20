import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.errors import (
    AppError,
    app_error_handler,
    db_error_handler,
    unexpected_error_handler,
    validation_error_handler,
)
from app.core.startup import sapu_proses_tergantung
from app.routers import auth, batch, health, ringkasan

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("storage_backend_aktif backend=%s", settings.STORAGE_BACKEND)
    async with AsyncSessionLocal() as db:
        await sapu_proses_tergantung(db)
    yield


app = FastAPI(title="Koreksi-in", lifespan=lifespan)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(DBAPIError, db_error_handler)
app.add_exception_handler(Exception, unexpected_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(ringkasan.router, prefix="/api")
