from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_stand_booking_schema import (
    EventStandBookingCreateSchema,
    EventStandBookingResponseSchema,
    UserEventStandSchema,
)
from app.domain.users.services.event_stand_booking_service import EventStandBookingService

router = APIRouter(prefix="/user", tags=["User - Event Stands"])


@router.get("/events/{event_id}/stands", response_model=list[UserEventStandSchema])
def list_event_stands_for_user(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventStandBookingService.list_event_stands_for_user(db, event_id, user.id)


@router.get("/stand-bookings", response_model=list[EventStandBookingResponseSchema])
def list_my_stand_bookings(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventStandBookingService.list_my_bookings(db, user.id)


@router.post("/stand-bookings", response_model=EventStandBookingResponseSchema, status_code=status.HTTP_201_CREATED)
def create_stand_booking(
    body: EventStandBookingCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventStandBookingService.create_booking(db, body.stand_session_id, user)


@router.delete("/stand-bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_stand_booking(
    booking_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    EventStandBookingService.cancel_booking(db, booking_id, user)
