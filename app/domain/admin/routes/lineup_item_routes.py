# app/domain/admin/routes/lineup_item_routes.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.domain.admin.services.lineup_item_service import LineupItemService
from app.core.security.permissions import require_subadmin_or_master
from app.domain.auth.models.user_model import User
from app.domain.admin.schemas.lineup_item_schema import (
    LineupItemCreateSchema,
    LineupItemUpdateSchema,
    LineupItemResponseSchema,
    LineupItemReorderSchema
)
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/admin", tags=["Admin - Lineup"])


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
    "/lineup-items",
    response_model=LineupItemResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def create_lineup_item(
    event_id: int = Form(...),
    artist_name: str = Form(...),
    performance_time: str = Form(...),  # Formato: HH:mm
    performance_end_time: str = Form(None),  # Formato: HH:mm
    stage: str = Form(None),
    event_date: str = Form(None),  # Formato: YYYY-MM-DD
    artist_image: UploadFile = File(None),
    display_order: Optional[int] = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Cria um novo item do lineup"""
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
        
        # Upload da imagem se fornecida
        artist_image_url = None
        if artist_image and artist_image.filename:
            try:
                artist_image_url = upload_image_to_s3(artist_image, folder="lineup")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao fazer upload da imagem: {str(e)}"
                )
        
        data = {
            "event_id": event_id,
            "artist_name": artist_name,
            "artist_image_url": artist_image_url,
            "performance_time": performance_time_obj,
            "performance_end_time": performance_end_time_obj,
            "stage": stage if stage else None,
            "event_date": event_date_obj,
            "display_order": display_order,
            "description": description if description else None
        }
        
        lineup_item = LineupItemService.create_lineup_item(db, data, user)
        return lineup_item
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        # Se a mensagem contém "não encontrado", é 404, senão é erro de validação (400)
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
            detail=f"Erro ao criar item do lineup: {str(e)}"
        )


@router.get(
    "/events/{event_id}/lineup-items",
    response_model=List[LineupItemResponseSchema]
)
def get_lineup_items_by_event(
    event_id: int,
    db: Session = Depends(get_admin_db)
):
    """Busca todos os itens do lineup de um evento"""
    try:
        lineup_items = LineupItemService.get_lineup_items_by_event(db, event_id)
        return lineup_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar itens do lineup: {str(e)}"
        )


@router.get(
    "/lineup-items/{lineup_item_id}",
    response_model=LineupItemResponseSchema
)
def get_lineup_item(
    lineup_item_id: int,
    db: Session = Depends(get_admin_db)
):
    """Busca um item do lineup por ID"""
    try:
        lineup_item = LineupItemService.get_lineup_item_by_id(db, lineup_item_id)
        if not lineup_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item do lineup não encontrado"
            )
        return lineup_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar item do lineup: {str(e)}"
        )


@router.put(
    "/lineup-items/{lineup_item_id}",
    response_model=LineupItemResponseSchema
)
def update_lineup_item(
    lineup_item_id: int,
    artist_name: str = Form(None),
    performance_time: str = Form(None),  # Formato: HH:mm
    performance_end_time: str = Form(None),  # Formato: HH:mm
    stage: str = Form(None),
    event_date: str = Form(None),  # Formato: YYYY-MM-DD
    artist_image: UploadFile = File(None),
    display_order: Optional[int] = Form(None),
    description: str = Form(None),
    remove_image: bool = Form(False),  # Se True, remove a imagem existente
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Atualiza um item do lineup"""
    try:
        data = {}
        
        if artist_name is not None:
            data["artist_name"] = artist_name
        
        if performance_time is not None:
            data["performance_time"] = parse_time_string(performance_time)
        
        if performance_end_time is not None:
            data["performance_end_time"] = parse_time_string(performance_end_time) if performance_end_time and performance_end_time.strip() else None
        
        if stage is not None:
            data["stage"] = stage if stage and stage.strip() else None
        
        if event_date is not None:
            data["event_date"] = parse_date_string(event_date) if event_date and event_date.strip() else None
        
        if display_order is not None:
            data["display_order"] = display_order
        
        if description is not None:
            data["description"] = description if description else None
        
        # Upload da nova imagem se fornecida
        if artist_image and artist_image.filename:
            try:
                artist_image_url = upload_image_to_s3(artist_image, folder="lineup")
                data["artist_image_url"] = artist_image_url
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao fazer upload da imagem: {str(e)}"
                )
        elif remove_image:
            data["artist_image_url"] = None
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar foi fornecido"
            )
        
        lineup_item = LineupItemService.update_lineup_item(db, lineup_item_id, data, user)
        return lineup_item
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        # Se a mensagem contém "não encontrado", é 404, senão é erro de validação (400)
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
            detail=f"Erro ao atualizar item do lineup: {str(e)}"
        )


@router.patch(
    "/events/{event_id}/lineup-items/reorder",
    response_model=List[LineupItemResponseSchema]
)
def reorder_lineup_items(
    event_id: int,
    payload: LineupItemReorderSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Reordena os artistas do lineup de um dia especifico"""
    try:
        lineup_items = LineupItemService.reorder_lineup_items(
            db,
            event_id,
            payload.event_date,
            payload.item_ids,
            user
        )
        return lineup_items
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        error_msg = str(e)
        if "nao encontrado" in error_msg.lower() or "não encontrado" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao reordenar lineup: {str(e)}"
        )


@router.delete(
    "/lineup-items/{lineup_item_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_lineup_item(
    lineup_item_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Deleta um item do lineup"""
    try:
        LineupItemService.delete_lineup_item(db, lineup_item_id, user)
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
            detail=f"Erro ao deletar item do lineup: {str(e)}"
        )


@router.post(
    "/events/{event_id}/notify-lineup-updated",
    status_code=status.HTTP_200_OK
)
def notify_lineup_updated(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Notifica todos os usuários sobre atualização do lineup"""
    try:
        from app.domain.users.tasks.notification_tasks import notify_lineup_updated_task
        notify_lineup_updated_task.delay(event_id)
        return {"message": "Notificações enviadas com sucesso"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar notificações: {str(e)}"
        )
