from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db as get_auth_db
from app.core.security.permissions import require_admin_or_master, require_operador_or_above
from app.infra.s3_upload import upload_image_to_s3
from app.domain.admin.schemas.food_order_schema import FoodOrderResponseSchema, OrderStatusUpdateSchema
from app.domain.admin.schemas.menu_item_schema import MenuItemCreateSchema, MenuItemResponseSchema, MenuItemUpdateSchema
from app.domain.admin.schemas.restaurant_schema import RestaurantCreateSchema, RestaurantResponseSchema, RestaurantUpdateSchema
from app.domain.admin.services.restaurant_service import RestaurantService
from app.domain.auth.models.user_model import User
from app.domain.users.services.food_order_service import FoodOrderService

router = APIRouter(tags=["Admin - Restaurantes"])


def _attach_user_info(orders, auth_db: Session):
    """Busca nome e CPF dos usuários no banco de auth e anexa às orders."""
    if not orders:
        return
    user_ids = list({o.user_id for o in orders})
    users = auth_db.query(User.id, User.name, User.cpf).filter(User.id.in_(user_ids)).all()
    info = {u.id: u for u in users}
    for o in orders:
        u = info.get(o.user_id)
        o.user_name = u.name if u else None
        o.user_cpf = u.cpf if u else None


# ── Restaurants ───────────────────────────────────────────────────────────────

@router.post("/admin/restaurants", response_model=RestaurantResponseSchema, status_code=201)
def create_restaurant(
    data: RestaurantCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return RestaurantService.create(db, data, user.id)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get("/admin/events/{event_id}/restaurants", response_model=List[RestaurantResponseSchema])
def list_restaurants_admin(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    return RestaurantService.get_by_event(db, event_id)


@router.get("/admin/restaurants/{restaurant_id}", response_model=RestaurantResponseSchema)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return RestaurantService.get_by_id(db, restaurant_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@router.put("/admin/restaurants/{restaurant_id}", response_model=RestaurantResponseSchema)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return RestaurantService.update(db, restaurant_id, data, user.id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@router.patch("/admin/restaurants/{restaurant_id}/image", response_model=RestaurantResponseSchema)
def upload_restaurant_image(
    restaurant_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    from app.domain.admin.models.restaurant_model import Restaurant
    rest = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.deleted_at.is_(None)).first()
    if not rest:
        raise HTTPException(404, detail="Restaurante não encontrado.")
    url = upload_image_to_s3(image, folder="restaurants")
    rest.image_url = url
    db.commit()
    db.refresh(rest)
    return rest


@router.delete("/admin/restaurants/{restaurant_id}", status_code=204)
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        RestaurantService.delete(db, restaurant_id, user.id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


# ── Menu items ────────────────────────────────────────────────────────────────

@router.post("/admin/menu-items", response_model=MenuItemResponseSchema, status_code=201)
def create_menu_item(
    data: MenuItemCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return RestaurantService.create_item(db, data, user.id)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get("/admin/restaurants/{restaurant_id}/menu-items", response_model=List[MenuItemResponseSchema])
def list_menu_items_admin(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    return RestaurantService.get_items(db, restaurant_id)


@router.put("/admin/menu-items/{item_id}", response_model=MenuItemResponseSchema)
def update_menu_item(
    item_id: int,
    data: MenuItemUpdateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return RestaurantService.update_item(db, item_id, data, user.id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


@router.patch("/admin/menu-items/{item_id}/image", response_model=MenuItemResponseSchema)
def upload_menu_item_image(
    item_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    from app.domain.admin.models.menu_item_model import MenuItem
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.deleted_at.is_(None)).first()
    if not item:
        raise HTTPException(404, detail="Item não encontrado.")
    url = upload_image_to_s3(image, folder="menu_items")
    item.image_url = url
    db.commit()
    db.refresh(item)
    return item


@router.delete("/admin/menu-items/{item_id}", status_code=204)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        RestaurantService.delete_item(db, item_id, user.id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e))


# ── Operation: list all restaurants ──────────────────────────────────────────

@router.get("/operation/restaurants", response_model=List[RestaurantResponseSchema])
def operation_list_restaurants(
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_operador_or_above),
):
    """Retorna todos os restaurantes ativos (para admins no painel de operação)"""
    from app.domain.admin.models.restaurant_model import Restaurant
    return db.query(Restaurant).filter(
        Restaurant.deleted_at.is_(None),
        Restaurant.is_active.is_(True),
    ).order_by(Restaurant.name.asc()).all()


class RestaurantWithMenuSchema(RestaurantResponseSchema):
    menu_items: List = []


@router.get("/operation/restaurant/{restaurant_id}")
def operation_get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_operador_or_above),
):
    """Retorna restaurante + cardápio para a tela de operação do operador"""
    from app.domain.admin.models.restaurant_model import Restaurant
    from app.domain.admin.models.menu_item_model import MenuItem
    from app.domain.admin.schemas.menu_item_schema import MenuItemResponseSchema

    rest = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.deleted_at.is_(None),
    ).first()
    if not rest:
        raise HTTPException(404, detail="Restaurante não encontrado.")

    items = db.query(MenuItem).filter(
        MenuItem.restaurant_id == restaurant_id,
        MenuItem.deleted_at.is_(None),
        MenuItem.is_available.is_(True),
    ).order_by(MenuItem.category.asc(), MenuItem.name.asc()).all()

    return {
        "id": rest.id,
        "event_id": rest.event_id,
        "name": rest.name,
        "description": rest.description,
        "image_url": rest.image_url,
        "is_active": rest.is_active,
        "menu_items": [
            {
                "id": i.id,
                "restaurant_id": i.restaurant_id,
                "name": i.name,
                "description": i.description,
                "price": float(i.price),
                "category": i.category,
                "image_url": i.image_url,
                "is_available": i.is_available,
            }
            for i in items
        ],
    }


# ── Kitchen endpoints ─────────────────────────────────────────────────────────

@router.get("/kitchen/restaurants/{restaurant_id}/orders", response_model=List[FoodOrderResponseSchema])
def kitchen_list_orders(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_auth_db),
    user: User = Depends(require_operador_or_above),
):
    orders = FoodOrderService.get_restaurant_orders(db, restaurant_id, statuses=["pending", "preparing"])
    for o in orders:
        o.restaurant_name = o.restaurant.name if o.restaurant else None
    _attach_user_info(orders, auth_db)
    return orders


@router.patch("/kitchen/orders/{order_id}/status", response_model=FoodOrderResponseSchema)
def kitchen_update_status(
    order_id: int,
    body: OrderStatusUpdateSchema,
    db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_auth_db),
    user: User = Depends(require_operador_or_above),
):
    try:
        order = FoodOrderService.update_status(db, order_id, body.status)
        order.restaurant_name = order.restaurant.name if order.restaurant else None
        _attach_user_info([order], auth_db)
        return order
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


# ── Waiter endpoints ──────────────────────────────────────────────────────────

@router.get("/waiter/restaurants/{restaurant_id}/orders", response_model=List[FoodOrderResponseSchema])
def waiter_list_orders(
    restaurant_id: int,
    db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_auth_db),
    user: User = Depends(require_operador_or_above),
):
    orders = FoodOrderService.get_restaurant_orders(db, restaurant_id, statuses=["ready"])
    for o in orders:
        o.restaurant_name = o.restaurant.name if o.restaurant else None
    _attach_user_info(orders, auth_db)
    return orders


@router.patch("/waiter/orders/{order_id}/delivered", response_model=FoodOrderResponseSchema)
def waiter_deliver_order(
    order_id: int,
    db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_auth_db),
    user: User = Depends(require_operador_or_above),
):
    try:
        order = FoodOrderService.update_status(db, order_id, "delivered")
        order.restaurant_name = order.restaurant.name if order.restaurant else None
        _attach_user_info([order], auth_db)
        return order
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
