from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.schemas.event_camping_session_schema import (
    EventCampingSessionCreateSchema,
    EventCampingSessionResponseSchema,
    EventCampingSessionUpdateSchema,
)
from app.domain.admin.services.event_camping_session_service import EventCampingSessionService
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/admin", tags=["Admin - Camping Sessions"])


class GenerateDailySessionsBody(BaseModel):
    start_date: date
    end_date: date
    capacity: int = 1


@router.post("/events/{event_id}/camping/generate-daily-sessions")
def generate_daily_sessions(
    event_id: int,
    body: GenerateDailySessionsBody,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingSessionService.generate_daily_sessions(
            db, event_id, body.start_date, body.end_date, body.capacity, user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/camping-areas/{area_id}/sessions",
    response_model=EventCampingSessionResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_camping_session(
    area_id: int,
    body: EventCampingSessionCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingSessionService.create_session(db, area_id, body.model_dump(), user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/events/{event_id}/camping/sessions",
    response_model=List[EventCampingSessionResponseSchema],
)
def get_camping_sessions_by_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingSessionService.get_sessions_by_event(db, event_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/camping-areas/{area_id}/sessions",
    response_model=List[EventCampingSessionResponseSchema],
)
def get_camping_sessions_by_area(
    area_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingSessionService.get_sessions_by_area(db, area_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/camping-sessions/{session_id}",
    response_model=EventCampingSessionResponseSchema,
)
def get_camping_session(
    session_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingSessionService.get_session_by_id(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/camping-sessions/{session_id}",
    response_model=EventCampingSessionResponseSchema,
)
def update_camping_session(
    session_id: int,
    body: EventCampingSessionUpdateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        return EventCampingSessionService.update_session(db, session_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/camping-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_camping_session(
    session_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        EventCampingSessionService.delete_session(db, session_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
