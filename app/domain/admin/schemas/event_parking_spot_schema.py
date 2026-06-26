from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ParkingSpotCreateSchema(BaseModel):
    event_id: int
    label: str
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    capacity: int = 1
    is_active: bool = True
    sort_order: int = 0


class ParkingSpotUpdateSchema(BaseModel):
    label: Optional[str] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ParkingSpotResponseSchema(BaseModel):
    id: int
    event_id: int
    label: str
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    capacity: int
    is_active: bool
    sort_order: int
    booked_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParkingMapResponseSchema(BaseModel):
    image_url: Optional[str] = None
    spots: list[ParkingSpotResponseSchema]
