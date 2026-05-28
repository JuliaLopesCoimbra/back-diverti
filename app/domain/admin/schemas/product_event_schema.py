# app/domain/admin/schemas/product_event_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class ProductEventImageSchema(BaseModel):
    id: int
    product_id: int
    image_url: str
    image_order: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductEventCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    status: Optional[str] = "active"
    stock: Optional[int] = 0
    last_pieces: Optional[bool] = False
    event_id: int

class ProductEventResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    status: str
    stock: int
    last_pieces: bool
    event_id: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    images: List[ProductEventImageSchema] = []

    class Config:
        from_attributes = True

class ProductEventUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    status: Optional[str] = None
    stock: Optional[int] = None
    last_pieces: Optional[bool] = None
    event_id: Optional[int] = None

