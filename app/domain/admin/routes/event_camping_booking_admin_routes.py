from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db as get_auth_db
from app.core.security.permissions import require_admin_or_master
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_camping_booking_schema import (
    AdminCampingSessionBookingResponseSchema,
    CampingBookingCheckInByTokenSchema,
)
from app.domain.users.services.event_camping_booking_service import EventCampingBookingService

router = APIRouter(prefix="/admin", tags=["Admin - Camping Bookings"])


@router.get(
    "/camping-sessions/{session_id}/bookings",
    response_model=List[AdminCampingSessionBookingResponseSchema],
)
def list_camping_session_bookings(
    session_id: int,
    admin_db: Session = Depends(get_admin_db),
    auth_db: Session = Depends(get_auth_db),
    user: User = Depends(require_admin_or_master),
):
    return EventCampingBookingService.list_session_bookings(admin_db, auth_db, session_id)


@router.post(
    "/camping-bookings/{booking_id}/check-in",
    response_model=AdminCampingSessionBookingResponseSchema,
)
def check_in_camping_booking(
    booking_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingBookingService.check_in_booking(db, booking_id, user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/camping-bookings/check-in-by-token",
)
def check_in_camping_booking_by_token(
    body: CampingBookingCheckInByTokenSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingBookingService.check_in_by_token(db, body.token, user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
