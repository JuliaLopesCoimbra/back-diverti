from typing import Optional
from pydantic import BaseModel


class RestaurantCreateSchema(BaseModel):
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


class RestaurantUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantResponseSchema(BaseModel):
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True
