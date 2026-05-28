from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel


class EventStandSessionCreateSchema(BaseModel):
    stand_id: int
    session_date: date
    start_time: time
    end_time: Optional[time] = None
    booking_open_time: Optional[time] = None
    capacity: int = 100
    status: str = "active"


class EventStandSessionUpdateSchema(BaseModel):
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    booking_open_time: Optional[time] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class EventStandSessionResponseSchema(BaseModel):
    id: int
    stand_id: int
    session_date: date
    start_time: time
    end_time: Optional[time] = None
    booking_open_time: Optional[time] = None
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
