from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.admin.models.event_parking_spot_model import EventParkingSpot
from app.domain.admin.models.parking_booking_model import ParkingBooking


class EventParkingRepository:

    # ── Spots ────────────────────────────────────────────────────────────────

    @staticmethod
    def get_spots_by_event(db: Session, event_id: int) -> list:
        spots = (
            db.query(EventParkingSpot)
            .filter(EventParkingSpot.event_id == event_id, EventParkingSpot.deleted_at.is_(None))
            .order_by(EventParkingSpot.sort_order, EventParkingSpot.created_at)
            .all()
        )
        for spot in spots:
            spot.booked_count = (
                db.query(func.count(ParkingBooking.id))
                .filter(ParkingBooking.parking_spot_id == spot.id, ParkingBooking.status == "active")
                .scalar()
            )
        return spots

    @staticmethod
    def get_active_spots_by_event(db: Session, event_id: int) -> list:
        spots = (
            db.query(EventParkingSpot)
            .filter(
                EventParkingSpot.event_id == event_id,
                EventParkingSpot.is_active.is_(True),
                EventParkingSpot.deleted_at.is_(None),
            )
            .order_by(EventParkingSpot.sort_order, EventParkingSpot.created_at)
            .all()
        )
        for spot in spots:
            spot.booked_count = (
                db.query(func.count(ParkingBooking.id))
                .filter(ParkingBooking.parking_spot_id == spot.id, ParkingBooking.status == "active")
                .scalar()
            )
        return spots

    @staticmethod
    def get_spot(db: Session, spot_id: int) -> Optional[EventParkingSpot]:
        return db.query(EventParkingSpot).filter(
            EventParkingSpot.id == spot_id,
            EventParkingSpot.deleted_at.is_(None),
        ).first()

    @staticmethod
    def create_spot(db: Session, data: dict) -> EventParkingSpot:
        spot = EventParkingSpot(**data)
        db.add(spot)
        db.commit()
        db.refresh(spot)
        spot.booked_count = 0
        return spot

    @staticmethod
    def update_spot(db: Session, spot: EventParkingSpot, data: dict) -> EventParkingSpot:
        for key, value in data.items():
            setattr(spot, key, value)
        db.commit()
        db.refresh(spot)
        spot.booked_count = (
            db.query(func.count(ParkingBooking.id))
            .filter(ParkingBooking.parking_spot_id == spot.id, ParkingBooking.status == "active")
            .scalar()
        )
        return spot

    @staticmethod
    def soft_delete_spot(db: Session, spot: EventParkingSpot, deleted_by_id: int) -> None:
        spot.deleted_at = datetime.now(timezone.utc)
        spot.deleted_by_id = deleted_by_id
        db.commit()

    # ── Bookings ─────────────────────────────────────────────────────────────

    @staticmethod
    def get_my_booking_for_event(db: Session, user_id: int, event_id: int) -> Optional[ParkingBooking]:
        return db.query(ParkingBooking).filter(
            ParkingBooking.user_id == user_id,
            ParkingBooking.event_id == event_id,
            ParkingBooking.status == "active",
        ).first()

    @staticmethod
    def get_my_bookings(db: Session, user_id: int) -> list:
        return (
            db.query(ParkingBooking)
            .filter(ParkingBooking.user_id == user_id, ParkingBooking.status == "active")
            .order_by(ParkingBooking.created_at.desc())
            .all()
        )

    @staticmethod
    def get_booking(db: Session, booking_id: int) -> Optional[ParkingBooking]:
        return db.query(ParkingBooking).filter(ParkingBooking.id == booking_id).first()

    @staticmethod
    def create_booking(db: Session, data: dict) -> ParkingBooking:
        booking = ParkingBooking(**data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def cancel_booking(db: Session, booking: ParkingBooking, cancelled_by_user_id: Optional[int] = None, cancelled_by_admin_id: Optional[int] = None) -> None:
        booking.status = "cancelled"
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancelled_by_user_id = cancelled_by_user_id
        booking.cancelled_by_admin_id = cancelled_by_admin_id
        db.commit()

    @staticmethod
    def get_bookings_by_event(db: Session, event_id: int) -> list:
        return (
            db.query(ParkingBooking)
            .filter(ParkingBooking.event_id == event_id, ParkingBooking.status == "active")
            .order_by(ParkingBooking.created_at.desc())
            .all()
        )
