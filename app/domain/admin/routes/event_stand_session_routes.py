from datetime import date, time
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.schemas.event_stand_session_schema import EventStandSessionResponseSchema
from app.domain.admin.services.event_stand_session_service import EventStandSessionService
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/admin", tags=["Admin - Event Stand Sessions"])


def parse_time_string(value: Optional[str]) -> Optional[time]:
    if value is None or not value.strip():
        return None
    try:
        return time.fromisoformat(value.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de horario invalido: {value}. Use HH:MM",
        )


def parse_date_string(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de data invalido: {value}. Use YYYY-MM-DD",
        )


@router.post(
    "/event-stands/{stand_id}/sessions",
    response_model=EventStandSessionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_event_stand_session(
    stand_id: int,
    session_date: str = Form(...),
    start_time: str = Form(...),
    end_time: Optional[str] = Form(None),
    booking_open_time: Optional[str] = Form(None),
    capacity: int = Form(100),
    status_value: str = Form("active", alias="status"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventStandSessionService.create_session(
            db,
            stand_id,
            {
                "session_date": parse_date_string(session_date),
                "start_time": parse_time_string(start_time),
                "end_time": parse_time_string(end_time),
                "booking_open_time": parse_time_string(booking_open_time),
                "capacity": capacity,
                "status": status_value,
            },
            user,
        )
    except ValueError as e:
        message = str(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "encontrado" in message else status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


@router.get(
    "/event-stands/{stand_id}/sessions",
    response_model=List[EventStandSessionResponseSchema],
)
def get_event_stand_sessions(
    stand_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventStandSessionService.get_sessions_by_stand(db, stand_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/event-stand-sessions/{session_id}",
    response_model=EventStandSessionResponseSchema,
)
def get_event_stand_session(
    session_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventStandSessionService.get_session_by_id(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/event-stand-sessions/{session_id}",
    response_model=EventStandSessionResponseSchema,
)
def update_event_stand_session(
    session_id: int,
    session_date: Optional[str] = Form(None),
    start_time: Optional[str] = Form(None),
    end_time: Optional[str] = Form(None),
    booking_open_time: Optional[str] = Form(None),
    capacity: Optional[int] = Form(None),
    status_value: Optional[str] = Form(None, alias="status"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        data = {}
        if session_date is not None:
            data["session_date"] = parse_date_string(session_date)
        if start_time is not None:
            data["start_time"] = parse_time_string(start_time)
        if end_time is not None:
            data["end_time"] = parse_time_string(end_time)
        if booking_open_time is not None:
            data["booking_open_time"] = parse_time_string(booking_open_time)
        if capacity is not None:
            data["capacity"] = capacity
        if status_value is not None:
            data["status"] = status_value

        return EventStandSessionService.update_session(db, session_id, data, user)
    except ValueError as e:
        message = str(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "encontrada" in message or "encontrado" in message else status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


@router.delete(
    "/event-stand-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event_stand_session(
    session_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        EventStandSessionService.delete_session(db, session_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
