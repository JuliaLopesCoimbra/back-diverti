from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CampingPackageCreateSchema(BaseModel):
    event_id: int
    label: str
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    price_cents: int = 0
    price_label: Optional[str] = None
    period: Optional[str] = None
    days: Optional[List[str]] = None
    is_active: bool = True
    sort_order: int = 0


class CampingPackageUpdateSchema(BaseModel):
    label: Optional[str] = None
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    price_cents: Optional[int] = None
    price_label: Optional[str] = None
    period: Optional[str] = None
    days: Optional[List[str]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CampingPackageResponseSchema(BaseModel):
    id: int
    event_id: int
    label: str
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    price_cents: int
    price_label: Optional[str] = None
    period: Optional[str] = None
    days: Optional[List[str]] = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
