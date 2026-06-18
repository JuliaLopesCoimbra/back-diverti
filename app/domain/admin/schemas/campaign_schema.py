# app/domain/admin/schemas/campaign_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CampaignCreateRequest(BaseModel):
    campaign_name: str
    ad_type: str  # "CPC" or "CPV"
    creative_url: Optional[str] = None
    creative_name: Optional[str] = None
    redirect_url: Optional[str] = None
    event_id: Optional[int] = None
    target_units: Optional[int] = 1000
    budget_type: Optional[str] = "total"  # "diario" or "total"
    budget_value: Optional[float] = 0.0
    start_at: Optional[datetime] = None
    duration_days: Optional[int] = 7
    hobbies: Optional[List[str]] = None
    professions: Optional[List[str]] = None
    gender: Optional[str] = "todos"
    age_min: Optional[int] = 18
    age_max: Optional[int] = 65
    address: Optional[str] = None
    radius_km: Optional[float] = 10.0
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    status: Optional[str] = "active"

class CampaignResponse(BaseModel):
    id: int
    patrocinador_id: int
    campaign_name: str
    ad_type: str
    creative_url: Optional[str] = None
    creative_name: Optional[str] = None
    redirect_url: Optional[str] = None
    event_id: Optional[int] = None
    target_units: int
    budget_type: str
    budget_value: float
    start_at: Optional[datetime] = None
    duration_days: Optional[int] = None
    hobbies: Optional[List] = None
    professions: Optional[List] = None
    gender: Optional[str] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    address: Optional[str] = None
    radius_km: Optional[float] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatrocinadorWithCampaigns(BaseModel):
    patrocinador_id: int
    patrocinador_name: Optional[str] = None
    patrocinador_email: Optional[str] = None
    campaigns: List[CampaignResponse] = []
