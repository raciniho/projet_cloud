from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from sqlmodel import SQLModel, Field

class FileMetadata(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    filename: str
    size: int
    content_type: str
    hash: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    minio_object_name: str
