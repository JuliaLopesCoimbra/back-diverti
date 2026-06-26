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
    cpc: float | None = None
    cpv: float | None = None
    min_radius: float | None = None
    min_duration: int | None = None
    min_units: int | None = None
    max_budget: float | None = None
    new_sponsors: bool | None = None
    email_notifications: bool | None = None
    auto_approve: bool | None = None
    maintenance_mode: bool | None = None
