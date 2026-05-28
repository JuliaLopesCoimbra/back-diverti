from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.event_stand_session_model import EventStandSession


class EventStandSessionRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventStandSession:
        session = EventStandSession(**data)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get(db: Session, session_id: int, include_deleted: bool = False) -> Optional[EventStandSession]:
        query = db.query(EventStandSession).filter(EventStandSession.id == session_id)
        if not include_deleted:
            query = query.filter(EventStandSession.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_stand(db: Session, stand_id: int, include_deleted: bool = False) -> list[EventStandSession]:
        query = db.query(EventStandSession).filter(EventStandSession.stand_id == stand_id)
        if not include_deleted:
            query = query.filter(EventStandSession.deleted_at.is_(None))
        return query.order_by(EventStandSession.session_date.asc(), EventStandSession.start_time.asc()).all()

    @staticmethod
    def get_by_stand_ids(db: Session, stand_ids: list[int], include_deleted: bool = False) -> list[EventStandSession]:
        if not stand_ids:
            return []

        query = db.query(EventStandSession).filter(EventStandSession.stand_id.in_(stand_ids))
        if not include_deleted:
            query = query.filter(EventStandSession.deleted_at.is_(None))
        return query.order_by(EventStandSession.session_date.asc(), EventStandSession.start_time.asc()).all()

    @staticmethod
    def update(db: Session, session: EventStandSession, data: dict) -> EventStandSession:
        clearable_fields = {"end_time", "booking_open_time"}
        for key, value in data.items():
            if value is not None or key in clearable_fields:
                setattr(session, key, value)

        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def soft_delete(db: Session, session: EventStandSession, deleted_by_id: int) -> EventStandSession:
        session.deleted_at = datetime.utcnow()
        session.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(session)
        return session
