from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.admin.repositories.food_order_repository import FoodOrderRepository
from app.domain.admin.repositories.menu_item_repository import MenuItemRepository
from app.domain.admin.repositories.restaurant_repository import RestaurantRepository
from app.domain.admin.schemas.food_order_schema import FoodOrderCreateSchema

VALID_TRANSITIONS = {
    "pending": ["preparing", "cancelled"],
    "preparing": ["ready", "cancelled"],
    "ready": ["delivered"],
    "delivered": [],
    "cancelled": [],
}


class FoodOrderService:
    @staticmethod
    def create_order(db: Session, data: FoodOrderCreateSchema, user_id: int):
        restaurant = RestaurantRepository.get(db, data.restaurant_id)
        if not restaurant or not restaurant.is_active:
            raise ValueError("Restaurante indisponível")

        item_rows = []
        total = Decimal("0")
        for req in data.items:
            menu_item = MenuItemRepository.get(db, req.menu_item_id)
            if not menu_item or not menu_item.is_available:
                raise ValueError(f"Item '{req.menu_item_id}' indisponível")
            if req.quantity < 1:
                raise ValueError("Quantidade mínima é 1")
            subtotal = Decimal(str(menu_item.price)) * req.quantity
            total += subtotal
            item_rows.append({
                "menu_item_id": menu_item.id,
                "item_name": menu_item.name,
                "unit_price": menu_item.price,
                "quantity": req.quantity,
                "subtotal": subtotal,
            })

        order_data = {
            "user_id": user_id,
            "restaurant_id": data.restaurant_id,
            "event_id": data.event_id,
            "delivery_spot": data.delivery_spot,
            "notes": data.notes,
            "status": "pending",
            "total": total,
        }
        return FoodOrderRepository.create(db, order_data, item_rows)

    @staticmethod
    def get_my_orders(db: Session, user_id: int):
        orders = FoodOrderRepository.get_by_user(db, user_id)
        for o in orders:
            o.restaurant_name = o.restaurant.name if o.restaurant else None
        return orders

    @staticmethod
    def get_restaurant_orders(db: Session, restaurant_id: int, statuses: list[str] | None = None):
        return FoodOrderRepository.get_by_restaurant(db, restaurant_id, statuses=statuses)

    @staticmethod
    def update_status(db: Session, order_id: int, new_status: str):
        order = FoodOrderRepository.get(db, order_id)
        if not order:
            raise ValueError("Pedido não encontrado")
        allowed = VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise ValueError(f"Transição inválida: {order.status} → {new_status}")
        return FoodOrderRepository.update_status(db, order, new_status)
