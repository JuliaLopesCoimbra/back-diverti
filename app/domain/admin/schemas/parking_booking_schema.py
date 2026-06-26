from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParkingBookingCreateSchema(BaseModel):
    parking_spot_id: int
    event_id: int


class ParkingBookingResponseSchema(BaseModel):
    id: int
    user_id: int
    event_id: int
    parking_spot_id: int
    status: str
    qr_token: str
    spot_label: Optional[str] = None
    created_at: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True
