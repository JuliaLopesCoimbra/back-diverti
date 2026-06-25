from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventCampingAreaCreateSchema(BaseModel):
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_spots: int = 100
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class EventCampingAreaUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_spots: Optional[int] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class EventCampingAreaResponseSchema(BaseModel):
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_spots: int
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    created_at: datetime
    created_by_id: int
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None

    class Config:
        from_attributes = True
