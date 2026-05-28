from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.repositories.lineup_item_repository import LineupItemRepository
from app.domain.admin.repositories.parade_lineup_item_repository import ParadeLineupItemRepository
from app.domain.admin.services.parade_lineup_item_service import ParadeLineupItemService
from app.domain.admin.schemas.event_schema import EventResponseSchema
from app.domain.admin.schemas.lineup_item_schema import LineupItemResponseSchema
from app.domain.admin.schemas.parade_lineup_item_schema import ParadeLineupItemResponseSchema
from typing import List

router = APIRouter(prefix="/public", tags=["Public - Events"])


@router.get("/events", response_model=list[EventResponseSchema])
def list_events_public(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de eventos (1-100)"),
    offset: int = Query(0, ge=0, description="Número de eventos para pular"),
    db: Session = Depends(get_admin_db)
):
    """Endpoint público para listar eventos ativos com paginação obrigatória"""
    return EventRepository.list_active(db, limit, offset)


@router.get("/events/{event_id}", response_model=EventResponseSchema)
def get_event_public(
    event_id: int,
    db: Session = Depends(get_admin_db)
):
    """Endpoint público para buscar um evento ativo por ID"""
    try:
        event = EventRepository.get_by_id(db, event_id, include_deleted=False)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        # Se veio do cache como dict, verifica se está ativo
        if isinstance(event, dict):
            if not event.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Evento não encontrado"
                )
            return EventResponseSchema(**event)
        
        # Se for objeto SQLAlchemy, verifica se está ativo
        if not event.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evento não encontrado"
            )
        
        return EventResponseSchema.model_validate(event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar evento: {str(e)}"
        )


@router.get("/events/{event_id}/lineup-items", response_model=List[LineupItemResponseSchema])
def get_lineup_items_public(
    event_id: int,
    db: Session = Depends(get_admin_db)
):
    """Endpoint público para buscar os itens do lineup de um evento"""
    items = LineupItemRepository.get_by_event_id(db, event_id)
    # Sempre retorna uma lista, mesmo que vazia
    return items if items else []


@router.get("/events/{event_id}/parade-lineup-items", response_model=List[ParadeLineupItemResponseSchema])
def get_parade_lineup_items_public(
    event_id: int,
    db: Session = Depends(get_admin_db)
):
    """Endpoint público para buscar os itens do lineup de desfile de um evento"""
    items = ParadeLineupItemService.get_parade_lineup_items_by_event(db, event_id)
    # Sempre retorna uma lista, mesmo que vazia
    return items if items else []

