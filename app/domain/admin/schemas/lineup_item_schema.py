# app/domain/admin/schemas/lineup_item_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime, date

class LineupItemCreateSchema(BaseModel):
    event_id: int
    artist_name: str
    artist_image_url: Optional[str] = None
    performance_time: time
    performance_end_time: Optional[time] = None
    stage: Optional[str] = None
    event_date: Optional[date] = None
    display_order: Optional[int] = None
    description: Optional[str] = None

class LineupItemUpdateSchema(BaseModel):
    artist_name: Optional[str] = None
    artist_image_url: Optional[str] = None
    performance_time: Optional[time] = None
    performance_end_time: Optional[time] = None
    stage: Optional[str] = None
    event_date: Optional[date] = None
    display_order: Optional[int] = None
    description: Optional[str] = None

class LineupItemResponseSchema(BaseModel):
    id: int
    event_id: int
    artist_name: str
    artist_image_url: Optional[str] = None
    performance_time: time
    performance_end_time: Optional[time] = None
    stage: Optional[str] = None
    event_date: Optional[date] = None
    display_order: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LineupItemReorderSchema(BaseModel):
    event_date: Optional[date] = None
    item_ids: list[int]

