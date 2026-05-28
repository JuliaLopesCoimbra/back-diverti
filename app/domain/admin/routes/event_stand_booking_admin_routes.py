from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.core.security.permissions import require_admin_or_master
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_stand_booking_schema import (
    AdminStandSessionBookingResponseSchema,
    StandBookingCheckInByTokenSchema,
)
from app.domain.users.services.event_stand_booking_service import EventStandBookingService

router = APIRouter(prefix="/admin", tags=["Admin - Event Stand Bookings"])


@router.get(
    "/event-stand-sessions/{session_id}/bookings",
    response_model=list[AdminStandSessionBookingResponseSchema],
)
def list_session_bookings(
    session_id: int,
    admin_db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_db),
    user: User = Depends(require_admin_or_master),
):
    return EventStandBookingService.list_session_bookings(admin_db, auth_db, session_id)


@router.post(
    "/event-stand-bookings/{booking_id}/check-in",
    status_code=status.HTTP_200_OK,
)
def check_in_booking(
    booking_id: int,
    admin_db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    EventStandBookingService.check_in_booking(admin_db, booking_id, user)
    return {"message": "Entrada registrada com sucesso"}


@router.post(
    "/event-stand-bookings/check-in-by-token",
    status_code=status.HTTP_200_OK,
)
def check_in_booking_by_token(
    body: StandBookingCheckInByTokenSchema,
    admin_db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    return EventStandBookingService.check_in_by_token(admin_db, body.token, user)
