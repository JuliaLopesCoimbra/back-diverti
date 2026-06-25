from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.schemas.event_camping_area_schema import EventCampingAreaResponseSchema
from app.domain.admin.services.event_camping_area_service import EventCampingAreaService
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/admin", tags=["Admin - Camping Areas"])


@router.post(
    "/camping-areas",
    response_model=EventCampingAreaResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_camping_area(
    event_id: int = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    total_spots: int = Form(100),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    x_position: Optional[float] = Form(None),
    y_position: Optional[float] = Form(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        resolved_image_url = None
        if image and image.filename:
            resolved_image_url = upload_image_to_s3(image, folder="camping_areas")
        elif image_url:
            resolved_image_url = image_url

        return EventCampingAreaService.create_area(
            db,
            {
                "event_id": event_id,
                "name": name.strip(),
                "description": description.strip() if description else None,
                "image_url": resolved_image_url,
                "total_spots": total_spots,
                "x_position": x_position,
                "y_position": y_position,
            },
            user,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar area: {str(e)}")


@router.get(
    "/events/{event_id}/camping-areas",
    response_model=List[EventCampingAreaResponseSchema],
)
def get_camping_areas_by_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingAreaService.get_areas_by_event(db, event_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/camping-areas/{area_id}",
    response_model=EventCampingAreaResponseSchema,
)
def get_camping_area(
    area_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        return EventCampingAreaService.get_area_by_id(db, area_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/camping-areas/{area_id}",
    response_model=EventCampingAreaResponseSchema,
)
def update_camping_area(
    area_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    total_spots: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    remove_image: bool = Form(False),
    x_position: Optional[float] = Form(None),
    y_position: Optional[float] = Form(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        data = {}
        if name is not None:
            data["name"] = name.strip()
        if description is not None:
            data["description"] = description.strip() if description.strip() else None
        if total_spots is not None:
            data["total_spots"] = total_spots
        if remove_image:
            data["image_url"] = None
        elif image and image.filename:
            data["image_url"] = upload_image_to_s3(image, folder="camping_areas")
        elif image_url is not None:
            data["image_url"] = image_url
        if x_position is not None:
            data["x_position"] = x_position
        if y_position is not None:
            data["y_position"] = y_position

        return EventCampingAreaService.update_area(db, area_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/camping-areas/{area_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_camping_area(
    area_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):
    try:
        EventCampingAreaService.delete_area(db, area_id, user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
