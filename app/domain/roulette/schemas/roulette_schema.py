from typing import Optional
from pydantic import BaseModel

class RouletteCreateSchema(BaseModel):
    name: str

class RouletteResponseSchema(BaseModel):
    id: int
    event_id: int
    name: str
    is_active: bool
    roulette_image_url: Optional[str]
    pointer_image_url: Optional[str]
    expires_at: Optional[str]

    class Config:
        from_attributes = True