from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class FoodOrderItemCreateSchema(BaseModel):
    menu_item_id: int
    quantity: int


class FoodOrderCreateSchema(BaseModel):
    restaurant_id: int
    event_id: int
    delivery_spot: Optional[str] = None
    notes: Optional[str] = None
    items: list[FoodOrderItemCreateSchema]


class FoodOrderItemResponseSchema(BaseModel):
    id: int
    menu_item_id: Optional[int] = None
    item_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal

    class Config:
        from_attributes = True


class FoodOrderResponseSchema(BaseModel):
    id: int
    user_id: int
    restaurant_id: int
    event_id: int
    delivery_spot: Optional[str] = None
    notes: Optional[str] = None
    status: str
    total: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    restaurant_name: Optional[str] = None
    user_name: Optional[str] = None
    user_cpf: Optional[str] = None
    items: list[FoodOrderItemResponseSchema] = []

    class Config:
        from_attributes = True


class OrderStatusUpdateSchema(BaseModel):
    status: str
