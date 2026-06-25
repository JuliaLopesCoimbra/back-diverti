from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.event_camping_session_model import EventCampingSession


class EventCampingSessionRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventCampingSession:
        session = EventCampingSession(**data)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get(db: Session, session_id: int, include_deleted: bool = False) -> Optional[EventCampingSession]:
        query = db.query(EventCampingSession).filter(EventCampingSession.id == session_id)
        if not include_deleted:
            query = query.filter(EventCampingSession.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_area(db: Session, area_id: int, include_deleted: bool = False) -> list[EventCampingSession]:
        query = db.query(EventCampingSession).filter(EventCampingSession.area_id == area_id)
        if not include_deleted:
            query = query.filter(EventCampingSession.deleted_at.is_(None))
        return query.order_by(EventCampingSession.check_in_date.asc()).all()

    @staticmethod
    def get_by_area_ids(db: Session, area_ids: list[int], include_deleted: bool = False) -> list[EventCampingSession]:
        if not area_ids:
            return []
        query = db.query(EventCampingSession).filter(EventCampingSession.area_id.in_(area_ids))
        if not include_deleted:
            query = query.filter(EventCampingSession.deleted_at.is_(None))
        return query.order_by(EventCampingSession.check_in_date.asc()).all()

    @staticmethod
    def update(db: Session, session: EventCampingSession, data: dict) -> EventCampingSession:
        for key, value in data.items():
            if value is not None:
                setattr(session, key, value)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def soft_delete(db: Session, session: EventCampingSession, deleted_by_id: int) -> EventCampingSession:
        session.deleted_at = datetime.utcnow()
        session.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(session)
        return session
