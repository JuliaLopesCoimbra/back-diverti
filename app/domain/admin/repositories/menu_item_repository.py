from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.menu_item_model import MenuItem


class MenuItemRepository:
    @staticmethod
    def create(db: Session, data: dict) -> MenuItem:
        obj = MenuItem(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get(db: Session, item_id: int) -> Optional[MenuItem]:
        return db.query(MenuItem).filter(
            MenuItem.id == item_id,
            MenuItem.deleted_at.is_(None),
        ).first()

    @staticmethod
    def get_by_restaurant(db: Session, restaurant_id: int, available_only: bool = False) -> list[MenuItem]:
        q = db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.deleted_at.is_(None),
        )
        if available_only:
            q = q.filter(MenuItem.is_available.is_(True))
        return q.order_by(MenuItem.category.asc(), MenuItem.name.asc()).all()

    @staticmethod
    def update(db: Session, obj: MenuItem, data: dict) -> MenuItem:
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def soft_delete(db: Session, obj: MenuItem, deleted_by_id: int) -> None:
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by_id = deleted_by_id
        db.commit()
