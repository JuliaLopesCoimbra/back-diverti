# app/domain/admin/schemas/ad_click_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class AdClickCreateSchema(BaseModel):
    event_id: int
    ad_identifier: str
    ad_url: Optional[str] = None
    redirect_url: Optional[str] = None

class AdClickResponseSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_id: int
    ad_identifier: str
    ad_url: Optional[str] = None
    redirect_url: Optional[str] = None
    clicked_at: datetime

    class Config:
        from_attributes = True

class AdClickStatsSchema(BaseModel):
    ad_identifier: str
    total_clicks: int
    clicks_by_hour: Dict[str, int]  # { "hour": count }
    clicks_by_event: Dict[str, int]  # { "event_id": count }
    first_click: Optional[datetime] = None
    last_click: Optional[datetime] = None

class AdClickStatsResponseSchema(BaseModel):
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    total_clicks: int
    clicks_by_ad: list[AdClickStatsSchema]
    clicks_by_hour: Dict[str, int]  # { "hour": count }
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

# Schemas para Views
class AdViewCreateSchema(BaseModel):
    event_id: int
    ad_identifier: str
    ad_url: Optional[str] = None

class AdViewResponseSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_id: int
    ad_identifier: str
    ad_url: Optional[str] = None
    viewed_at: datetime

    class Config:
        from_attributes = True

class AdViewStatsSchema(BaseModel):
    ad_identifier: str
    total_views: int
    views_by_hour: Dict[str, int]
    views_by_event: Dict[str, int]
    first_view: Optional[datetime] = None
    last_view: Optional[datetime] = None

class AdViewStatsResponseSchema(BaseModel):
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    total_views: int
    views_by_ad: list[AdViewStatsSchema]
    views_by_hour: Dict[str, int]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

