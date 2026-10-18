from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.errors import AppError, app_error_handler, validation_error_handler
from app.routers import auth, batch, health

app = FastAPI(title="Koreksi-in")

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
