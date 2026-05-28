# app/domain/admin/routes/ad_click_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.config.admin_db import get_admin_db
from app.domain.admin.controllers.ad_click_controller import AdClickController
from app.domain.admin.schemas.ad_click_schema import (
    AdClickCreateSchema,
    AdClickResponseSchema,
    AdClickStatsResponseSchema,
    AdViewCreateSchema,
    AdViewStatsResponseSchema
)
from app.core.security.auth_dependency import get_current_user_optional
from app.domain.auth.models.user_model import User
from app.infra.redis import check_rate_limit
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ads", tags=["Ad Clicks"])

@router.post(
    "/clicks",
    response_model=AdClickResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def register_ad_click(
    click_data: AdClickCreateSchema,
    request: Request,
    db: Session = Depends(get_admin_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Registra um clique em um anúncio com rate limiting"""
    # Rate limiting: 30 cliques por minuto por IP
    ip = request.client.host
    identifier = f"ad_click:ip:{ip}"
    allowed, remaining = check_rate_limit(identifier, max_requests=30, window_seconds=60, critical=False)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições. Tente novamente em alguns instantes.",
            headers={"X-RateLimit-Remaining": str(remaining), "Retry-After": "60"}
        )
    
    try:
        user_id = user.id if user else None
        return AdClickController.create_click(db, click_data, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao registrar clique: {str(e)}"
        )

@router.get(
    "/stats",
    response_model=AdClickStatsResponseSchema
)
def get_ad_stats(
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    ad_identifier: Optional[str] = Query(None, description="Filtrar por anúncio"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_admin_db)
):
    """Obtém estatísticas de cliques de anúncios"""
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        return AdClickController.get_stats(
            db,
            event_id=event_id,
            ad_identifier=ad_identifier,
            start_date=start_dt,
            end_date=end_dt
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de data inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )

@router.post(
    "/views",
    status_code=status.HTTP_202_ACCEPTED  # 202 = Accepted (processando em background)
)
def register_ad_view(
    view_data: AdViewCreateSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Registra uma visualização de forma ASSÍNCRONA usando batch processing
    Retorna 202 Accepted imediatamente - processamento em background
    """
    # Rate limiting: 10 views por minuto por IP
    ip = request.client.host
    identifier = f"ad_view:ip:{ip}"
    allowed, remaining = check_rate_limit(identifier, max_requests=10, window_seconds=60, critical=False)
    
    if not allowed:
        # Para views, retornamos 202 mesmo com rate limit (silent fail)
        return {"status": "rate_limited", "message": "View not registered"}
    
    user_id = user.id if user else None
    
    # Envia para Celery (processo separado) - não bloqueia
    # Se Celery não estiver disponível, usa fallback local
    try:
        AdClickController.queue_view_for_batch(
            view_data.event_id,
            view_data.ad_identifier,
            view_data.ad_url,
            user_id
        )
    except Exception as e:
        # Se tudo falhar, loga mas não quebra a requisição
        logger.error(f"Erro ao enfileirar view: {e}", exc_info=True)
    
    # Retorna imediatamente (202 Accepted)
    return {
        "status": "accepted",
        "message": "View queued for processing"
    }

@router.get(
    "/views/stats",
    response_model=AdViewStatsResponseSchema
)
def get_ad_view_stats(
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    ad_identifier: Optional[str] = Query(None, description="Filtrar por anúncio"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_admin_db)
):
    """Obtém estatísticas de visualizações de anúncios"""
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        return AdClickController.get_view_stats(
            db,
            event_id=event_id,
            ad_identifier=ad_identifier,
            start_date=start_dt,
            end_date=end_dt
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de data inválido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )

