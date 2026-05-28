from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel


class EventStandBookingCreateSchema(BaseModel):
    stand_session_id: int


class UserStandSessionSummarySchema(BaseModel):
    id: int
    stand_id: int
    session_date: date
    start_time: time
    end_time: Optional[time] = None
    booking_open_time: Optional[time] = None
    capacity: int
    status: str
    booked_slots: int
    remaining_slots: int
    is_booked: bool


class UserEventStandSchema(BaseModel):
    id: int
    event_id: int
    name: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    sessions: List[UserStandSessionSummarySchema] = []


class EventStandBookingResponseSchema(BaseModel):
    id: int
    user_id: int
    stand_session_id: int
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by_admin_id: Optional[int] = None
    stand_id: int
    stand_name: str
    stand_image_url: Optional[str] = None
    event_id: int
    event_title: Optional[str] = None
    session_date: date
    start_time: time
    end_time: Optional[time] = None
    booking_open_time: Optional[time] = None
    status: str
    qr_token: Optional[str] = None


class AdminStandSessionBookingResponseSchema(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    created_at: datetime
    checked_in_at: Optional[datetime] = None
    checked_in_by_admin_id: Optional[int] = None


class StandBookingCheckInByTokenSchema(BaseModel):
    token: str
