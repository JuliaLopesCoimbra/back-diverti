# app/domain/admin/routes/campaign_routes.py

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from typing import List

from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_admin_master
from app.domain.admin.controllers.campaign_controller import CampaignController
from app.domain.admin.schemas.campaign_schema import (
    CampaignCreateRequest,
    CampaignResponse,
    PatrocinadorWithCampaigns,
)
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    body: CampaignCreateRequest,
    db_admin: Session = Depends(get_admin_db),
    db_auth: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Patrocinador ou admin_master cria uma campanha."""
    if current_user.role not in ["patrocinador", "admin_master"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas patrocinadores podem criar campanhas.",
        )
    try:
        return CampaignController.create_campaign(db_admin, db_auth, body, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar campanha: {str(e)}",
        )


@router.get("/my", response_model=List[CampaignResponse])
def list_my_campaigns(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db_admin: Session = Depends(get_admin_db),
    current_user: User = Depends(get_current_user),
):
    """Patrocinador lista suas próprias campanhas."""
    if current_user.role not in ["patrocinador", "admin_master"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a patrocinadores.",
        )
    try:
        return CampaignController.list_my_campaigns(db_admin, current_user, limit, offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar campanhas: {str(e)}",
        )


@router.post("/upload-creative")
def upload_creative(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Patrocinador faz upload do criativo (imagem/vídeo) para S3."""
    if current_user.role not in ["patrocinador", "admin_master", "admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "video/mp4", "video/quicktime"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não suportado: {file.content_type}.")
    try:
        url = upload_image_to_s3(file, folder="campaign_creatives")
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@router.get("/all", response_model=List[PatrocinadorWithCampaigns])
def list_all_grouped(
    db_admin: Session = Depends(get_admin_db),
    db_auth: Session = Depends(get_db),
    admin_master: User = Depends(require_admin_master),
):
    """Admin master visualiza todas as campanhas agrupadas por patrocinador."""
    try:
        return CampaignController.list_all_grouped(db_admin, db_auth)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar campanhas: {str(e)}",
        )
