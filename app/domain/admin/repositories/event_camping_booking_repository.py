from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domain.admin.models.event_camping_booking_model import EventCampingBooking
from app.domain.admin.models.event_camping_area_model import EventCampingArea
from app.domain.admin.models.event_camping_session_model import EventCampingSession


class EventCampingBookingRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventCampingBooking:
        booking = EventCampingBooking(**data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get(db: Session, booking_id: int) -> Optional[EventCampingBooking]:
        return (
            db.query(EventCampingBooking)
            .options(
                joinedload(EventCampingBooking.session)
                .joinedload(EventCampingSession.area)
                .joinedload(EventCampingArea.event)
            )
            .filter(EventCampingBooking.id == booking_id)
            .first()
        )

    @staticmethod
    def count_active_by_session(db: Session, camping_session_id: int) -> int:
        return (
            db.query(EventCampingBooking)
            .filter(
                EventCampingBooking.camping_session_id == camping_session_id,
                EventCampingBooking.cancelled_at.is_(None),
            )
            .count()
        )

    @staticmethod
    def get_active_by_user_and_session(db: Session, user_id: int, camping_session_id: int) -> Optional[EventCampingBooking]:
        return (
            db.query(EventCampingBooking)
            .filter(
                EventCampingBooking.user_id == user_id,
                EventCampingBooking.camping_session_id == camping_session_id,
                EventCampingBooking.cancelled_at.is_(None),
            )
            .first()
        )

    @staticmethod
    def count_active_grouped_by_session(db: Session, camping_session_ids: list[int]) -> dict[int, int]:
        if not camping_session_ids:
            return {}
        rows = (
            db.query(
                EventCampingBooking.camping_session_id,
                func.count(EventCampingBooking.id),
            )
            .filter(
                EventCampingBooking.camping_session_id.in_(camping_session_ids),
                EventCampingBooking.cancelled_at.is_(None),
            )
            .group_by(EventCampingBooking.camping_session_id)
            .all()
        )
        return {camping_session_id: total for camping_session_id, total in rows}

    @staticmethod
    def list_active_session_ids_by_user(db: Session, user_id: int, camping_session_ids: list[int]) -> set[int]:
        if not camping_session_ids:
            return set()
        rows = (
            db.query(EventCampingBooking.camping_session_id)
            .filter(
                EventCampingBooking.user_id == user_id,
                EventCampingBooking.camping_session_id.in_(camping_session_ids),
                EventCampingBooking.cancelled_at.is_(None),
            )
            .all()
        )
        return {camping_session_id for camping_session_id, in rows}

    @staticmethod
    def list_active_by_session(db: Session, camping_session_id: int) -> list[EventCampingBooking]:
        return (
            db.query(EventCampingBooking)
            .options(
                joinedload(EventCampingBooking.session)
                .joinedload(EventCampingSession.area)
                .joinedload(EventCampingArea.event)
            )
            .filter(
                EventCampingBooking.camping_session_id == camping_session_id,
                EventCampingBooking.cancelled_at.is_(None),
            )
            .order_by(EventCampingBooking.created_at.asc())
            .all()
        )

    @staticmethod
    def list_active_by_user(db: Session, user_id: int) -> list[EventCampingBooking]:
        return (
            db.query(EventCampingBooking)
            .options(
                joinedload(EventCampingBooking.session)
                .joinedload(EventCampingSession.area)
                .joinedload(EventCampingArea.event)
            )
            .filter(
                EventCampingBooking.user_id == user_id,
                EventCampingBooking.cancelled_at.is_(None),
            )
            .order_by(EventCampingBooking.created_at.desc())
            .all()
        )

    @staticmethod
    def cancel_by_user(db: Session, booking: EventCampingBooking, user_id: int) -> EventCampingBooking:
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by_user_id = user_id
        db.commit()
        db.refresh(booking)
        return booking
