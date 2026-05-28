from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.config.interaction_db import get_interaction_db
from app.core.security.auth_dependency import get_current_user
from app.domain.auth.models.user_model import User
from app.domain.users.controllers.downloaded_photo_controller import DownloadedPhotoController
from app.domain.users.schemas.downloaded_photo_schema import DownloadedPhotoResponse, CreateDownloadedPhotoRequest
from typing import List

router = APIRouter(prefix="/downloaded-photos", tags=["Downloaded Photos"])

@router.post("", response_model=DownloadedPhotoResponse, status_code=201)
def create_downloaded_photo(
    body: CreateDownloadedPhotoRequest,
    interaction_db: Session = Depends(get_interaction_db),
    current_user: User = Depends(get_current_user)
):
    return DownloadedPhotoController.create_downloaded_photo(
        interaction_db, 
        current_user.id, 
        body
    )

@router.get("", response_model=List[DownloadedPhotoResponse])
def get_my_downloaded_photos(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    interaction_db: Session = Depends(get_interaction_db),
    current_user: User = Depends(get_current_user)
):
    return DownloadedPhotoController.get_user_downloaded_photos(
        interaction_db,
        current_user.id,
        limit,
        offset
    )

