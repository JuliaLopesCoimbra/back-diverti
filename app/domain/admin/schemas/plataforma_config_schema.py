from typing import Optional

from pydantic import BaseModel


class PlataformaConfigResponse(BaseModel):
    cpc: float
    cpv: float
    min_radius: float
    min_duration: int
    min_units: int
    max_budget: float
    new_sponsors: bool
    email_notifications: bool
    auto_approve: bool
    maintenance_mode: bool

    class Config:
        from_attributes = True


class PlataformaConfigUpdateRequest(BaseModel):
    cpc: Optional[float] = None
    cpv: Optional[float] = None
    min_radius: Optional[float] = None
    min_duration: Optional[int] = None
    min_units: Optional[int] = None
    max_budget: Optional[float] = None
    new_sponsors: Optional[bool] = None
    email_notifications: Optional[bool] = None
    auto_approve: Optional[bool] = None
    maintenance_mode: Optional[bool] = None
