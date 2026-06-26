from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class CampingBookingCreateSchema(BaseModel):
    camping_session_id: int


class UserCampingSessionSummarySchema(BaseModel):
    id: int
    area_id: int
    label: str
    check_in_date: date
    check_out_date: date
    capacity: int
    status: str
    booked_slots: int
    remaining_slots: int
    is_booked: bool


class UserCampingAreaSchema(BaseModel):
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    total_spots: int
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    sessions: List[UserCampingSessionSummarySchema] = []


class CampingBookingResponseSchema(BaseModel):
    id: int
    user_id: int
    camping_session_id: int
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by_admin_id: Optional[int] = None
    area_id: int
    area_name: str
    area_image_url: Optional[str] = None
    event_id: int
    event_title: Optional[str] = None
    label: str
    check_in_date: date
    check_out_date: date
    status: str
    qr_token: Optional[str] = None


class AdminCampingSessionBookingResponseSchema(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    user_cpf: Optional[str] = None
    user_profile_photo: Optional[str] = None
    created_at: datetime
    checked_in_at: Optional[datetime] = None
    checked_in_by_admin_id: Optional[int] = None


class CampingBookingCheckInByTokenSchema(BaseModel):
    token: str
