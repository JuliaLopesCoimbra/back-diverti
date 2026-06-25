from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.event_camping_area_model import EventCampingArea


class EventCampingAreaRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventCampingArea:
        area = EventCampingArea(**data)
        db.add(area)
        db.commit()
        db.refresh(area)
        return area

    @staticmethod
    def get(db: Session, area_id: int, include_deleted: bool = False) -> Optional[EventCampingArea]:
        query = db.query(EventCampingArea).filter(EventCampingArea.id == area_id)
        if not include_deleted:
            query = query.filter(EventCampingArea.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_event(db: Session, event_id: int, include_deleted: bool = False) -> list[EventCampingArea]:
        query = db.query(EventCampingArea).filter(EventCampingArea.event_id == event_id)
        if not include_deleted:
            query = query.filter(EventCampingArea.deleted_at.is_(None))
        return query.order_by(EventCampingArea.created_at.desc()).all()

    @staticmethod
    def update(db: Session, area: EventCampingArea, data: dict) -> EventCampingArea:
        for key, value in data.items():
            if value is not None or key == "image_url":
                setattr(area, key, value)
        db.commit()
        db.refresh(area)
        return area

    @staticmethod
    def soft_delete(db: Session, area: EventCampingArea, deleted_by_id: int) -> EventCampingArea:
        area.deleted_at = datetime.utcnow()
        area.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(area)
        return area
