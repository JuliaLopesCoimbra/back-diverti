from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.domain.admin.models.food_order_model import FoodOrder
from app.domain.admin.models.food_order_item_model import FoodOrderItem


class FoodOrderRepository:
    @staticmethod
    def create(db: Session, data: dict, items: list[dict]) -> FoodOrder:
        order = FoodOrder(**data)
        db.add(order)
        db.flush()
        for item_data in items:
            item_data["order_id"] = order.id
            db.add(FoodOrderItem(**item_data))
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def get(db: Session, order_id: int) -> Optional[FoodOrder]:
        return (
            db.query(FoodOrder)
            .options(joinedload(FoodOrder.items), joinedload(FoodOrder.restaurant))
            .filter(FoodOrder.id == order_id)
            .first()
        )

    @staticmethod
    def get_by_user(db: Session, user_id: int) -> list[FoodOrder]:
        return (
            db.query(FoodOrder)
            .options(joinedload(FoodOrder.items), joinedload(FoodOrder.restaurant))
            .filter(FoodOrder.user_id == user_id)
            .order_by(FoodOrder.created_at.desc())
            .all()
        )

    @staticmethod
    def get_by_restaurant(db: Session, restaurant_id: int, statuses: list[str] | None = None) -> list[FoodOrder]:
        q = (
            db.query(FoodOrder)
            .options(joinedload(FoodOrder.items))
            .filter(FoodOrder.restaurant_id == restaurant_id)
        )
        if statuses:
            q = q.filter(FoodOrder.status.in_(statuses))
        return q.order_by(FoodOrder.created_at.asc()).all()

    @staticmethod
    def update_status(db: Session, order: FoodOrder, status: str) -> FoodOrder:
        order.status = status
        db.commit()
        db.refresh(order)
        return order
