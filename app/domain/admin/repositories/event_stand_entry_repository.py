from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.admin.models.event_stand_booking_model import EventStandBooking

from app.domain.admin.models.event_stand_entry_model import EventStandEntry


class EventStandEntryRepository:
    @staticmethod
    def create(db: Session, booking_id: int, admin_id: int) -> EventStandEntry:
        entry = EventStandEntry(booking_id=booking_id, admin_id=admin_id)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_by_booking(db: Session, booking_id: int) -> Optional[EventStandEntry]:
        return db.query(EventStandEntry).filter(EventStandEntry.booking_id == booking_id).first()

    @staticmethod
    def count_by_session(db: Session, stand_session_id: int) -> int:
        return (
            db.query(EventStandEntry)
            .join(EventStandBooking, EventStandEntry.booking_id == EventStandBooking.id)
            .filter(
                EventStandBooking.stand_session_id == stand_session_id,
                EventStandBooking.cancelled_at.is_(None),
            )
            .count()
        )

    @staticmethod
    def count_grouped_by_session(db: Session, stand_session_ids: list[int]) -> dict[int, int]:
        if not stand_session_ids:
            return {}

        rows = (
            db.query(
                EventStandBooking.stand_session_id,
                func.count(EventStandEntry.id),
            )
            .join(EventStandBooking, EventStandEntry.booking_id == EventStandBooking.id)
            .filter(
                EventStandBooking.stand_session_id.in_(stand_session_ids),
                EventStandBooking.cancelled_at.is_(None),
            )
            .group_by(EventStandBooking.stand_session_id)
            .all()
        )
        return {stand_session_id: total for stand_session_id, total in rows}
