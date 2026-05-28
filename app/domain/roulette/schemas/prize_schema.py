from typing import Optional
from pydantic import BaseModel

class PrizeCreateSchema(BaseModel):
    name: str
    probability: int

class PrizeResponseSchema(BaseModel):
    id: int
    name: str
    probability: int
    position: int
    image_url: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
