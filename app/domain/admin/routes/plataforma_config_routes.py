from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_admin_master
from app.domain.admin.controllers.plataforma_config_controller import PlataformaConfigController
from app.domain.admin.schemas.plataforma_config_schema import (
    PlataformaConfigResponse,
    PlataformaConfigUpdateRequest,
)
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/plataforma/config", tags=["Plataforma Config"])


@router.get("", response_model=PlataformaConfigResponse)
def get_config(
    db: Session = Depends(get_admin_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna a configuração atual da plataforma. Acessível por qualquer usuário autenticado."""
    try:
        return PlataformaConfigController.get(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar configurações: {str(e)}")


@router.put("", response_model=PlataformaConfigResponse)
def update_config(
    body: PlataformaConfigUpdateRequest,
    db: Session = Depends(get_admin_db),
    admin_master: User = Depends(require_admin_master),
):
    """Atualiza a configuração da plataforma. Restrito ao admin master."""
    try:
        return PlataformaConfigController.update(db, body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar configurações: {str(e)}")
