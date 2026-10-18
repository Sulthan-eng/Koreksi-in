import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import StatusBatch


class BuatBatchRequest(BaseModel):
    nama_batch: str = Field(max_length=100)


class BatchResponse(BaseModel):
    id_batch: uuid.UUID
    nama_batch: str
    status: StatusBatch
    dibuat_pada: datetime
