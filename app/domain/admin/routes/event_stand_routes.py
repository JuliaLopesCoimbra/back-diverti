from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.schemas.event_stand_schema import EventStandResponseSchema
from app.domain.admin.services.event_stand_service import EventStandService
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/admin", tags=["Admin - Event Stands"])


@router.post(
    "/event-stands",
    response_model=EventStandResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_event_stand(
    event_id: int = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        image_url = None
        if image and image.filename:
            image_url = upload_image_to_s3(image, folder="event_stands")

        return EventStandService.create_stand(
            db,
            {
                "event_id": event_id,
                "name": name.strip(),
                "description": description.strip() if description else None,
                "image_url": image_url,
            },
            user,
        )
    except ValueError as e:
        message = str(e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "Evento" in message else status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar estande: {str(e)}",
        )


@router.get(
    "/events/{event_id}/event-stands",
    response_model=List[EventStandResponseSchema],
)
def get_event_stands_by_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventStandService.get_stands_by_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar estandes: {str(e)}",
        )


@router.get(
    "/event-stands/{stand_id}",
    response_model=EventStandResponseSchema,
)
def get_event_stand(
    stand_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventStandService.get_stand_by_id(db, stand_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/event-stands/{stand_id}",
    response_model=EventStandResponseSchema,
)
def update_event_stand(
    stand_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        data = {}

        if name is not None:
            data["name"] = name.strip()
        if description is not None:
            data["description"] = description.strip() if description.strip() else None
        if remove_image:
            data["image_url"] = None
        if image and image.filename:
            data["image_url"] = upload_image_to_s3(image, folder="event_stands")

        return EventStandService.update_stand(db, stand_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar estande: {str(e)}",
        )


@router.delete(
    "/event-stands/{stand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event_stand(
    stand_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        EventStandService.delete_stand(db, stand_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
