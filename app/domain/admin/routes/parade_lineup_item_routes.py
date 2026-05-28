# app/domain/admin/routes/parade_lineup_item_routes.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.domain.admin.services.parade_lineup_item_service import ParadeLineupItemService
from app.core.security.permissions import require_subadmin_or_master
from app.domain.auth.models.user_model import User
from app.domain.admin.schemas.parade_lineup_item_schema import (
    ParadeLineupItemResponseSchema
)

router = APIRouter(prefix="/admin", tags=["Admin - Parade Lineup"])


def parse_time_string(time_str: str):
    """Parse time string from frontend (time format: HH:mm)"""
    from datetime import time
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            hour = int(parts[0])
            minute = int(parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Horário inválido")
            return time(hour, minute)
        else:
            raise ValueError("Formato de horário inválido. Use HH:mm")
    except (ValueError, IndexError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de horário inválido: {time_str}. Use HH:mm"
        )


def parse_date_string(date_str: str):
    """Parse date string from frontend (date format: YYYY-MM-DD)"""
    from datetime import date
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de data inválido: {date_str}. Use YYYY-MM-DD"
        )


@router.post(
    "/parade-lineup-items",
    response_model=ParadeLineupItemResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def create_parade_lineup_item(
    event_id: int = Form(...),
    samba_school_id: int = Form(...),
    performance_time: str = Form(...),  # Formato: HH:mm
    performance_end_time: str = Form(None),  # Formato: HH:mm
    event_date: str = Form(None),  # Formato: YYYY-MM-DD
    display_order: int = Form(0),
    description: str = Form(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Cria um novo item do lineup de desfile"""
    try:
        # Parse do horário
        performance_time_obj = parse_time_string(performance_time)
        
        # Parse do horário de término se fornecido
        performance_end_time_obj = None
        if performance_end_time:
            performance_end_time_obj = parse_time_string(performance_end_time)
        
        # Parse da data do evento se fornecida
        event_date_obj = None
        if event_date:
            event_date_obj = parse_date_string(event_date)
        
        data = {
            "event_id": event_id,
            "samba_school_id": samba_school_id,
            "performance_time": performance_time_obj,
            "performance_end_time": performance_end_time_obj,
            "event_date": event_date_obj,
            "display_order": display_order,
            "description": description if description else None
        }
        
        parade_lineup_item = ParadeLineupItemService.create_parade_lineup_item(db, data, user)
        # Retorna com dados da escola
        return ParadeLineupItemService.get_parade_lineup_item_by_id(db, parade_lineup_item.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        error_msg = str(e)
        if "não encontrado" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar item do lineup de desfile: {str(e)}"
        )


@router.get(
    "/events/{event_id}/parade-lineup-items",
    response_model=List[ParadeLineupItemResponseSchema]
)
def get_parade_lineup_items_by_event(
    event_id: int,
    db: Session = Depends(get_admin_db)
):
    """Busca todos os itens do lineup de desfile de um evento"""
    try:
        parade_lineup_items = ParadeLineupItemService.get_parade_lineup_items_by_event(db, event_id)
        return parade_lineup_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar itens do lineup de desfile: {str(e)}"
        )


@router.get(
    "/parade-lineup-items/{parade_lineup_item_id}",
    response_model=ParadeLineupItemResponseSchema
)
def get_parade_lineup_item(
    parade_lineup_item_id: int,
    db: Session = Depends(get_admin_db)
):
    """Busca um item do lineup de desfile por ID"""
    try:
        parade_lineup_item = ParadeLineupItemService.get_parade_lineup_item_by_id(db, parade_lineup_item_id)
        if not parade_lineup_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item do lineup de desfile não encontrado"
            )
        return parade_lineup_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar item do lineup de desfile: {str(e)}"
        )


@router.put(
    "/parade-lineup-items/{parade_lineup_item_id}",
    response_model=ParadeLineupItemResponseSchema
)
def update_parade_lineup_item(
    parade_lineup_item_id: int,
    samba_school_id: int = Form(None),
    performance_time: str = Form(None),  # Formato: HH:mm
    performance_end_time: str = Form(None),  # Formato: HH:mm
    event_date: str = Form(None),  # Formato: YYYY-MM-DD
    display_order: int = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Atualiza um item do lineup de desfile"""
    try:
        data = {}
        
        if samba_school_id is not None:
            data["samba_school_id"] = samba_school_id
        
        if performance_time is not None:
            data["performance_time"] = parse_time_string(performance_time)
        
        if performance_end_time is not None:
            data["performance_end_time"] = parse_time_string(performance_end_time) if performance_end_time and performance_end_time.strip() else None
        
        if event_date is not None:
            data["event_date"] = parse_date_string(event_date) if event_date and event_date.strip() else None
        
        if display_order is not None:
            data["display_order"] = display_order
        
        if description is not None:
            data["description"] = description if description else None
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar foi fornecido"
            )
        
        ParadeLineupItemService.update_parade_lineup_item(db, parade_lineup_item_id, data, user)
        return ParadeLineupItemService.get_parade_lineup_item_by_id(db, parade_lineup_item_id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        error_msg = str(e)
        if "não encontrado" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar item do lineup de desfile: {str(e)}"
        )


@router.delete(
    "/parade-lineup-items/{parade_lineup_item_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_parade_lineup_item(
    parade_lineup_item_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Deleta um item do lineup de desfile"""
    try:
        ParadeLineupItemService.delete_parade_lineup_item(db, parade_lineup_item_id, user)
        return None
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar item do lineup de desfile: {str(e)}"
        )




