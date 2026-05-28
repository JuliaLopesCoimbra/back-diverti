# app/domain/admin/schemas/parade_lineup_item_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime, date

class ParadeLineupItemCreateSchema(BaseModel):
    event_id: int
    samba_school_id: int
    performance_time: time
    performance_end_time: Optional[time] = None
    event_date: Optional[date] = None
    display_order: int = 0
    description: Optional[str] = None

class ParadeLineupItemUpdateSchema(BaseModel):
    samba_school_id: Optional[int] = None
    performance_time: Optional[time] = None
    performance_end_time: Optional[time] = None
    event_date: Optional[date] = None
    display_order: Optional[int] = None
    description: Optional[str] = None

class ParadeLineupItemResponseSchema(BaseModel):
    id: int
    event_id: int
    samba_school_id: int
    performance_time: time
    performance_end_time: Optional[time] = None
    event_date: Optional[date] = None
    display_order: int
    description: Optional[str] = None
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    # Dados da escola de samba
    samba_school_name: Optional[str] = None
    samba_school_image_url: Optional[str] = None

    class Config:
        from_attributes = True




