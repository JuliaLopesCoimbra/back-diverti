from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domain.admin.models.event_stand_booking_model import EventStandBooking
from app.domain.admin.models.event_stand_model import EventStand
from app.domain.admin.models.event_stand_session_model import EventStandSession


class EventStandBookingRepository:
    @staticmethod
    def create(db: Session, data: dict) -> EventStandBooking:
        booking = EventStandBooking(**data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get(db: Session, booking_id: int) -> Optional[EventStandBooking]:
        return (
            db.query(EventStandBooking)
            .options(
                joinedload(EventStandBooking.session)
                .joinedload(EventStandSession.stand)
                .joinedload(EventStand.event)
            )
            .filter(EventStandBooking.id == booking_id)
            .first()
        )

    @staticmethod
    def count_active_by_session(db: Session, stand_session_id: int) -> int:
        return (
            db.query(EventStandBooking)
            .filter(
                EventStandBooking.stand_session_id == stand_session_id,
                EventStandBooking.cancelled_at.is_(None),
            )
            .count()
        )

    @staticmethod
    def get_active_by_user_and_session(db: Session, user_id: int, stand_session_id: int) -> Optional[EventStandBooking]:
        return (
            db.query(EventStandBooking)
            .filter(
                EventStandBooking.user_id == user_id,
                EventStandBooking.stand_session_id == stand_session_id,
                EventStandBooking.cancelled_at.is_(None),
            )
            .first()
        )

    @staticmethod
    def count_active_grouped_by_session(db: Session, stand_session_ids: list[int]) -> dict[int, int]:
        if not stand_session_ids:
            return {}

        rows = (
            db.query(
                EventStandBooking.stand_session_id,
                func.count(EventStandBooking.id),
            )
            .filter(
                EventStandBooking.stand_session_id.in_(stand_session_ids),
                EventStandBooking.cancelled_at.is_(None),
            )
            .group_by(EventStandBooking.stand_session_id)
            .all()
        )
        return {stand_session_id: total for stand_session_id, total in rows}

    @staticmethod
    def list_active_session_ids_by_user(db: Session, user_id: int, stand_session_ids: list[int]) -> set[int]:
        if not stand_session_ids:
            return set()

        rows = (
            db.query(EventStandBooking.stand_session_id)
            .filter(
                EventStandBooking.user_id == user_id,
                EventStandBooking.stand_session_id.in_(stand_session_ids),
                EventStandBooking.cancelled_at.is_(None),
            )
            .all()
        )
        return {stand_session_id for stand_session_id, in rows}

    @staticmethod
    def list_active_by_session(db: Session, stand_session_id: int) -> list[EventStandBooking]:
        return (
            db.query(EventStandBooking)
            .options(
                joinedload(EventStandBooking.session)
                .joinedload(EventStandSession.stand)
                .joinedload(EventStand.event)
            )
            .filter(
                EventStandBooking.stand_session_id == stand_session_id,
                EventStandBooking.cancelled_at.is_(None),
            )
            .order_by(EventStandBooking.created_at.asc())
            .all()
        )

    @staticmethod
    def list_active_by_user(db: Session, user_id: int) -> list[EventStandBooking]:
        return (
            db.query(EventStandBooking)
            .options(
                joinedload(EventStandBooking.session)
                .joinedload(EventStandSession.stand)
                .joinedload(EventStand.event)
            )
            .filter(
                EventStandBooking.user_id == user_id,
                EventStandBooking.cancelled_at.is_(None),
            )
            .order_by(EventStandBooking.created_at.desc())
            .all()
        )

    @staticmethod
    def cancel_by_user(db: Session, booking: EventStandBooking, user_id: int) -> EventStandBooking:
        booking.cancelled_at = datetime.utcnow()
        booking.cancelled_by_user_id = user_id
        db.commit()
        db.refresh(booking)
        return booking
