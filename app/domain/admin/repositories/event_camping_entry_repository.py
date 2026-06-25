from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.admin.models.event_camping_entry_model import EventCampingEntry


class EventCampingEntryRepository:
    @staticmethod
    def create(db: Session, booking_id: int, admin_id: int) -> EventCampingEntry:
        entry = EventCampingEntry(booking_id=booking_id, admin_id=admin_id)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_by_booking(db: Session, booking_id: int) -> Optional[EventCampingEntry]:
        return db.query(EventCampingEntry).filter(EventCampingEntry.booking_id == booking_id).first()

    @staticmethod
    def count_by_session(db: Session, camping_session_id: int) -> int:
        from app.domain.admin.models.event_camping_booking_model import EventCampingBooking
        return (
            db.query(EventCampingEntry)
            .join(EventCampingBooking, EventCampingEntry.booking_id == EventCampingBooking.id)
            .filter(
                EventCampingBooking.camping_session_id == camping_session_id,
                EventCampingBooking.cancelled_at.is_(None),
            )
            .count()
        )

    @staticmethod
    def count_grouped_by_session(db: Session, camping_session_ids: list[int]) -> dict[int, int]:
        if not camping_session_ids:
            return {}
        from app.domain.admin.models.event_camping_booking_model import EventCampingBooking
        rows = (
            db.query(
                EventCampingBooking.camping_session_id,
                func.count(EventCampingEntry.id),
            )
            .join(EventCampingBooking, EventCampingEntry.booking_id == EventCampingBooking.id)
            .filter(
                EventCampingBooking.camping_session_id.in_(camping_session_ids),
                EventCampingBooking.cancelled_at.is_(None),
            )
            .group_by(EventCampingBooking.camping_session_id)
            .all()
        )
        return {camping_session_id: total for camping_session_id, total in rows}
