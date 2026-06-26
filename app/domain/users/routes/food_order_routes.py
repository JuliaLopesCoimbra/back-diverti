from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.domain.admin.schemas.food_order_schema import FoodOrderCreateSchema, FoodOrderResponseSchema
from app.domain.admin.schemas.menu_item_schema import MenuItemResponseSchema
from app.domain.admin.schemas.restaurant_schema import RestaurantResponseSchema
from app.domain.admin.services.restaurant_service import RestaurantService
from app.domain.auth.models.user_model import User
from app.domain.users.services.food_order_service import FoodOrderService

router = APIRouter(prefix="/user", tags=["User - Restaurantes"])


@router.get("/events/{event_id}/restaurants", response_model=List[RestaurantResponseSchema])
def list_restaurants_user(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return RestaurantService.get_by_event(db, event_id, active_only=True)


@router.get("/restaurants/{restaurant_id}/menu-items", response_model=List[MenuItemResponseSchema])
def list_menu_items_user(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return RestaurantService.get_items(db, restaurant_id, available_only=True)


@router.post("/food-orders", response_model=FoodOrderResponseSchema, status_code=201)
def create_food_order(
    data: FoodOrderCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    try:
        order = FoodOrderService.create_order(db, data, user.id)
        order.restaurant_name = order.restaurant.name if order.restaurant else None
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/food-orders", response_model=List[FoodOrderResponseSchema])
def list_my_food_orders(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return FoodOrderService.get_my_orders(db, user.id)
