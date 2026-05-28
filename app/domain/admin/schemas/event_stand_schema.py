from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventStandCreateSchema(BaseModel):
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class EventStandUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class EventStandResponseSchema(BaseModel):
    id: int
    event_id: int
    name: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    created_by_id: int
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None

    class Config:
        from_attributes = True
