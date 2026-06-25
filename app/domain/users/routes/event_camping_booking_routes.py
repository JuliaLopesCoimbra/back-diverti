from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_camping_booking_schema import (
    CampingBookingCreateSchema,
    CampingBookingResponseSchema,
    UserCampingAreaSchema,
)
from app.domain.users.services.event_camping_booking_service import EventCampingBookingService

router = APIRouter(prefix="/user", tags=["User - Camping"])


class BookDayBody(BaseModel):
    date: date


@router.get("/events/{event_id}/camping-areas", response_model=list[UserCampingAreaSchema])
def list_camping_areas_for_user(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventCampingBookingService.list_camping_areas_for_user(db, event_id, user.id)


@router.get("/camping-bookings", response_model=list[CampingBookingResponseSchema])
def list_my_camping_bookings(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventCampingBookingService.list_my_bookings(db, user.id)


@router.post(
    "/camping-bookings",
    response_model=CampingBookingResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_camping_booking(
    body: CampingBookingCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventCampingBookingService.create_booking(db, body.camping_session_id, user)


@router.post(
    "/camping-areas/{area_id}/book-day",
    response_model=CampingBookingResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def book_area_for_day(
    area_id: int,
    body: BookDayBody,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventCampingBookingService.book_area_for_day(db, area_id, body.date, user)


@router.delete("/camping-bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_camping_booking(
    booking_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    EventCampingBookingService.cancel_booking(db, booking_id, user)
