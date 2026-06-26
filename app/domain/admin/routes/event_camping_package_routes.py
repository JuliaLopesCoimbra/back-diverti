from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.repositories.event_camping_package_repository import EventCampingPackageRepository
from app.domain.admin.schemas.event_camping_package_schema import (
    CampingPackageCreateSchema,
    CampingPackageResponseSchema,
    CampingPackageUpdateSchema,
)

router = APIRouter(prefix="/admin", tags=["Admin - Camping Packages"])
public_router = APIRouter(prefix="/public", tags=["Public - Camping Packages"])


@router.get("/events/{event_id}/camping-packages", response_model=list[CampingPackageResponseSchema])
def list_packages(
    event_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    return EventCampingPackageRepository.get_by_event(db, event_id)


@router.post("/camping-packages", response_model=CampingPackageResponseSchema, status_code=status.HTTP_201_CREATED)
def create_package(
    body: CampingPackageCreateSchema,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    data = body.model_dump()
    data["created_by_id"] = current_user.id
    return EventCampingPackageRepository.create(db, data)


@router.put("/camping-packages/{package_id}", response_model=CampingPackageResponseSchema)
def update_package(
    package_id: int,
    body: CampingPackageUpdateSchema,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    pkg = EventCampingPackageRepository.get(db, package_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacote não encontrado")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    data["updated_by_id"] = current_user.id
    return EventCampingPackageRepository.update(db, pkg, data)


@router.delete("/camping-packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    pkg = EventCampingPackageRepository.get(db, package_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacote não encontrado")
    EventCampingPackageRepository.soft_delete(db, pkg, current_user.id)


@public_router.get("/events/{event_id}/camping-packages", response_model=list[CampingPackageResponseSchema])
def list_public_packages(
    event_id: int,
    db: Session = Depends(get_admin_db),
):
    return EventCampingPackageRepository.get_active_by_event(db, event_id)
