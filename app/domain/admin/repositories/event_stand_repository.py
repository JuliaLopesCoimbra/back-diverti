from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.event_stand_model import EventStand


class EventStandRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventStand:
        stand = EventStand(**data)
        db.add(stand)
        db.commit()
        db.refresh(stand)
        return stand

    @staticmethod
    def get(db: Session, stand_id: int, include_deleted: bool = False) -> Optional[EventStand]:
        query = db.query(EventStand).filter(EventStand.id == stand_id)
        if not include_deleted:
            query = query.filter(EventStand.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_event(db: Session, event_id: int, include_deleted: bool = False) -> list[EventStand]:
        query = db.query(EventStand).filter(EventStand.event_id == event_id)
        if not include_deleted:
            query = query.filter(EventStand.deleted_at.is_(None))
        return query.order_by(EventStand.created_at.desc()).all()

    @staticmethod
    def update(db: Session, stand: EventStand, data: dict) -> EventStand:
        for key, value in data.items():
            if value is not None or key == "image_url":
                setattr(stand, key, value)

        db.commit()
        db.refresh(stand)
        return stand

    @staticmethod
    def soft_delete(db: Session, stand: EventStand, deleted_by_id: int) -> EventStand:
        stand.deleted_at = datetime.utcnow()
        stand.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(stand)
        return stand
