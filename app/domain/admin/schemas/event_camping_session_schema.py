from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class EventCampingSessionCreateSchema(BaseModel):
    area_id: int
    label: str
    check_in_date: date
    check_out_date: date
    capacity: int = 100
    status: str = "active"


class EventCampingSessionUpdateSchema(BaseModel):
    label: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class EventCampingSessionResponseSchema(BaseModel):
    id: int
    area_id: int
    label: str
    check_in_date: date
    check_out_date: date
    capacity: int
    status: str
    created_at: datetime
    created_by_id: int
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    quantity_bookings: int = 0
    quantity_entries: int = 0
    quantity_missing_checkins: int = 0
    quantity_remaining_slots: int = 0

    class Config:
        from_attributes = True
