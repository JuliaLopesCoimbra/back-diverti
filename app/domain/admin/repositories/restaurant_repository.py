from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.restaurant_model import Restaurant


class RestaurantRepository:
    @staticmethod
    def create(db: Session, data: dict) -> Restaurant:
        obj = Restaurant(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def get(db: Session, restaurant_id: int) -> Optional[Restaurant]:
        return db.query(Restaurant).filter(
            Restaurant.id == restaurant_id,
            Restaurant.deleted_at.is_(None),
        ).first()

    @staticmethod
    def get_by_event(db: Session, event_id: int, active_only: bool = False) -> list[Restaurant]:
        q = db.query(Restaurant).filter(
            Restaurant.event_id == event_id,
            Restaurant.deleted_at.is_(None),
        )
        if active_only:
            q = q.filter(Restaurant.is_active.is_(True))
        return q.order_by(Restaurant.created_at.asc()).all()

    @staticmethod
    def update(db: Session, obj: Restaurant, data: dict) -> Restaurant:
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def soft_delete(db: Session, obj: Restaurant, deleted_by_id: int) -> None:
        obj.deleted_at = datetime.utcnow()
        obj.deleted_by_id = deleted_by_id
        db.commit()
