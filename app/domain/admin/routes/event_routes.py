from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, time
import json

from app.config.admin_db import get_admin_db
from app.domain.admin.controllers.event_controller import EventController
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_admin_or_master
from app.domain.auth.models.user_model import User
from app.domain.admin.schemas.event_schema import (
    EventResponseSchema, EventUpdateSchema
)
from app.infra.s3_upload import upload_image_to_s3, upload_event_map_images_to_s3

router = APIRouter(prefix="/admin", tags=["Admin - Events"])


from fastapi import Form, File, UploadFile
from typing import List

def parse_time_string(time_str: str) -> time:
    """Parse time string from frontend (time format: HH:mm)"""
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

def parse_datetime_string(dt_str: str) -> datetime:
    """Parse datetime string from frontend (datetime-local format: YYYY-MM-DDTHH:mm)"""
    try:
        # Tenta formato ISO com timezone
        if 'Z' in dt_str or '+' in dt_str or (dt_str.count('-') > 2 and 'T' in dt_str and ':' in dt_str):
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        # Formato datetime-local sem timezone (YYYY-MM-DDTHH:mm)
        # Assumimos que vem no timezone local e convertemos para UTC para comparação
        dt = datetime.fromisoformat(dt_str)
        # Se for naive datetime, assumimos que é UTC (ou podemos usar timezone local)
        # Para simplificar, vamos comparar como naive datetime com datetime.utcnow() também naive
        return dt
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de data inválido: {dt_str}"
        )

@router.post(
    "/events",
    response_model=EventResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def create_event(
    title: str = Form(...),
    description: str = Form(None),
    location: str = Form(None),
    starts_at: str = Form(None),
    ends_at: str = Form(None),
    event_dates: str = Form(None),  # Formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21"
    van_arrival_time_start: str = Form(None),  # Horário de início da ida (formato: HH:mm)
    van_arrival_time_end: str = Form(None),  # Horário de fim da ida (formato: HH:mm)
    van_departure_time_start: str = Form(None),  # Horário de início da volta (formato: HH:mm)
    van_departure_time_end: str = Form(None),  # Horário de fim da volta (formato: HH:mm)
    meeting_point_location: str = Form(None),  # Local do meeting point
    meeting_point_schedule: str = Form(None),  # Horários em formato JSON string
    line_up: str = Form(None),
    banner_image: UploadFile = File(None),
    map_images: List[UploadFile] = File(None),  # Múltiplas imagens do mapa (máximo 5)
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):

    # Validação de datas: não permitir datas no passado
    # Usamos datetime.now() para comparar com datetime-local (que vem sem timezone)
    now = datetime.now()
    
    if starts_at:
        try:
            starts_at_dt = parse_datetime_string(starts_at)
            # Remove timezone info se houver para comparação
            if starts_at_dt.tzinfo is not None:
                starts_at_dt = starts_at_dt.replace(tzinfo=None)
            if starts_at_dt <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de início deve ser no futuro"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data de início inválido"
            )
    
    if ends_at:
        try:
            ends_at_dt = parse_datetime_string(ends_at)
            # Remove timezone info se houver para comparação
            if ends_at_dt.tzinfo is not None:
                ends_at_dt = ends_at_dt.replace(tzinfo=None)
            if ends_at_dt <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de término deve ser no futuro"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data de término inválido"
            )
    
    # Validação: data de término deve ser após data de início
    if starts_at and ends_at:
        try:
            starts_at_dt = parse_datetime_string(starts_at)
            ends_at_dt = parse_datetime_string(ends_at)
            # Remove timezone info se houver para comparação
            if starts_at_dt.tzinfo is not None:
                starts_at_dt = starts_at_dt.replace(tzinfo=None)
            if ends_at_dt.tzinfo is not None:
                ends_at_dt = ends_at_dt.replace(tzinfo=None)
            if ends_at_dt <= starts_at_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de término deve ser posterior à data de início"
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Já foi validado acima

    banner_url = None
    if banner_image:
        banner_url = upload_image_to_s3(banner_image, folder="event_photos")

    # Validação: máximo de 5 imagens do mapa
    map_image_urls = []
    if map_images:
        if len(map_images) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo de 5 imagens do mapa permitidas"
            )

    # Converte strings de data para objetos datetime
    starts_at_dt = None
    ends_at_dt = None
    
    if starts_at:
        starts_at_dt = parse_datetime_string(starts_at)
    
    if ends_at:
        ends_at_dt = parse_datetime_string(ends_at)
    
    # Converte strings de horário para objetos time
    van_arrival_time_start_obj = None
    van_arrival_time_end_obj = None
    van_departure_time_start_obj = None
    van_departure_time_end_obj = None
    
    if van_arrival_time_start:
        van_arrival_time_start_obj = parse_time_string(van_arrival_time_start)
    
    if van_arrival_time_end:
        van_arrival_time_end_obj = parse_time_string(van_arrival_time_end)
    
    if van_departure_time_start:
        van_departure_time_start_obj = parse_time_string(van_departure_time_start)
    
    if van_departure_time_end:
        van_departure_time_end_obj = parse_time_string(van_departure_time_end)

    # Parse meeting_point_schedule JSON string
    meeting_point_schedule_obj = None
    if meeting_point_schedule:
        try:
            meeting_point_schedule_obj = json.loads(meeting_point_schedule)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato JSON inválido para meeting_point_schedule"
            )

    data = {
        "title": title,
        "description": description,
        "location": location,
        "banner_image": banner_url,
        "line_up": line_up,
        "starts_at": starts_at_dt,
        "ends_at": ends_at_dt,
        "event_dates": event_dates,
        "van_arrival_time_start": van_arrival_time_start_obj,
        "van_arrival_time_end": van_arrival_time_end_obj,
        "van_departure_time_start": van_departure_time_start_obj,
        "van_departure_time_end": van_departure_time_end_obj,
        "meeting_point_location": meeting_point_location,
        "meeting_point_schedule": meeting_point_schedule_obj
    }

    # Cria o evento primeiro para obter o ID
    event = EventController.create(db, data, user)
    
    # Faz upload das imagens do mapa e cria os registros
    if map_images and len(map_images) > 0:
        from app.domain.admin.models.event_map_image_model import EventMapImage
        map_image_urls = upload_event_map_images_to_s3(map_images, event.id, folder="map_images")
        
        # Cria os registros das imagens do mapa
        for index, image_url in enumerate(map_image_urls):
            map_image = EventMapImage(
                event_id=event.id,
                image_url=image_url,
                image_order=index
            )
            db.add(map_image)
        
        db.commit()
        db.refresh(event)
    
    return event


@router.get(
    "/events/{event_id}",
    response_model=EventResponseSchema
)
def get_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        event = EventController.get(db, event_id, user=None)
        # Se veio do cache como dict, converter diretamente
        # Se for objeto SQLAlchemy, o Pydantic converterá automaticamente
        if isinstance(event, dict):
            return EventResponseSchema(**event)
        else:
            return EventResponseSchema.model_validate(event)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/events", response_model=list[EventResponseSchema])
def list_events(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de eventos (1-100)"),
    offset: int = Query(0, ge=0, description="Número de eventos para pular"),
    db: Session = Depends(get_admin_db)
):
    return EventController.list(db, limit, offset)



@router.put(
    "/events/{event_id}",
    response_model=EventResponseSchema
)
def update_event(
    event_id: int,
    title: str = Form(...),
    description: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    location: str = Form(...),
    event_dates: str = Form(None),  # Formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21"
    van_arrival_time_start: str = Form(None),  # Horário de início da ida (formato: HH:mm)
    van_arrival_time_end: str = Form(None),  # Horário de fim da ida (formato: HH:mm)
    van_departure_time_start: str = Form(None),  # Horário de início da volta (formato: HH:mm)
    van_departure_time_end: str = Form(None),  # Horário de fim da volta (formato: HH:mm)
    meeting_point_location: str = Form(None),  # Local do meeting point
    meeting_point_schedule: str = Form(None),  # Horários em formato JSON string
    line_up: str = Form(None),
    banner_image: Optional[UploadFile] = File(None),
    map_images: Optional[List[UploadFile]] = File(None),  # Múltiplas imagens do mapa (máximo 5)
    replace_map_images: bool = Form(False),  # Se True, substitui todas as imagens antigas
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master),
):

    # Validação de datas: não permitir datas no passado
    # Usamos datetime.now() para comparar com datetime-local (que vem sem timezone)
    now = datetime.now()
    
    if start_date:
        try:
            start_date_dt = parse_datetime_string(start_date)
            # Remove timezone info se houver para comparação
            if start_date_dt.tzinfo is not None:
                start_date_dt = start_date_dt.replace(tzinfo=None)
            if start_date_dt <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de início deve ser no futuro"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data de início inválido"
            )
    
    if end_date:
        try:
            end_date_dt = parse_datetime_string(end_date)
            # Remove timezone info se houver para comparação
            if end_date_dt.tzinfo is not None:
                end_date_dt = end_date_dt.replace(tzinfo=None)
            if end_date_dt <= now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de término deve ser no futuro"
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de data de término inválido"
            )
    
    # Validação: data de término deve ser após data de início
    if start_date and end_date:
        try:
            start_date_dt = parse_datetime_string(start_date)
            end_date_dt = parse_datetime_string(end_date)
            # Remove timezone info se houver para comparação
            if start_date_dt.tzinfo is not None:
                start_date_dt = start_date_dt.replace(tzinfo=None)
            if end_date_dt.tzinfo is not None:
                end_date_dt = end_date_dt.replace(tzinfo=None)
            if end_date_dt <= start_date_dt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A data de término deve ser posterior à data de início"
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Já foi validado acima

    # Converte strings de data para objetos datetime
    starts_at_dt = None
    ends_at_dt = None
    
    if start_date:
        starts_at_dt = parse_datetime_string(start_date)
    
    if end_date:
        ends_at_dt = parse_datetime_string(end_date)
    
    # Converte strings de horário para objetos time
    van_arrival_time_start_obj = None
    van_arrival_time_end_obj = None
    van_departure_time_start_obj = None
    van_departure_time_end_obj = None
    
    if van_arrival_time_start:
        van_arrival_time_start_obj = parse_time_string(van_arrival_time_start)
    
    if van_arrival_time_end:
        van_arrival_time_end_obj = parse_time_string(van_arrival_time_end)
    
    if van_departure_time_start:
        van_departure_time_start_obj = parse_time_string(van_departure_time_start)
    
    if van_departure_time_end:
        van_departure_time_end_obj = parse_time_string(van_departure_time_end)

    # Parse meeting_point_schedule JSON string
    meeting_point_schedule_obj = None
    if meeting_point_schedule:
        try:
            meeting_point_schedule_obj = json.loads(meeting_point_schedule)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato JSON inválido para meeting_point_schedule"
            )

    data = {
        "title": title,
        "description": description,
        "starts_at": starts_at_dt,  # Nome correto do campo no modelo
        "ends_at": ends_at_dt,  # Nome correto do campo no modelo
        "location": location,
    }

    if event_dates:
        data["event_dates"] = event_dates

    if van_arrival_time_start_obj:
        data["van_arrival_time_start"] = van_arrival_time_start_obj

    if van_arrival_time_end_obj:
        data["van_arrival_time_end"] = van_arrival_time_end_obj

    if van_departure_time_start_obj:
        data["van_departure_time_start"] = van_departure_time_start_obj

    if van_departure_time_end_obj:
        data["van_departure_time_end"] = van_departure_time_end_obj

    if meeting_point_location:
        data["meeting_point_location"] = meeting_point_location

    if meeting_point_schedule_obj is not None:
        data["meeting_point_schedule"] = meeting_point_schedule_obj

    if line_up:
        data["line_up"] = line_up

    if banner_image:
        banner_url = upload_image_to_s3(
            banner_image,
            folder="event_photos"
        )
        data["banner_image"] = banner_url

    try:
        # Atualiza o evento primeiro
        event = EventController.update(db, event_id, data, user)
        
        # Processa as imagens do mapa
        if map_images and len(map_images) > 0:
            from app.domain.admin.models.event_map_image_model import EventMapImage
            
            # Validação: máximo de 5 imagens
            if len(map_images) > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Máximo de 5 imagens do mapa permitidas"
                )
            
            # Se replace_map_images=True, remove todas as imagens antigas
            if replace_map_images:
                db.query(EventMapImage).filter(EventMapImage.event_id == event_id).delete()
            
            # Faz upload das novas imagens
            map_image_urls = upload_event_map_images_to_s3(map_images, event_id, folder="map_images")
            
            # Cria os registros das imagens do mapa
            # Se não for replace, adiciona às existentes (verifica quantas já existem)
            existing_count = db.query(EventMapImage).filter(EventMapImage.event_id == event_id).count()
            start_order = existing_count if not replace_map_images else 0
            
            for index, image_url in enumerate(map_image_urls):
                map_image = EventMapImage(
                    event_id=event_id,
                    image_url=image_url,
                    image_order=start_order + index
                )
                db.add(map_image)
            
            db.commit()
            db.refresh(event)
        
        return event
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):

    try:
        EventController.delete(db, event_id, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/events/{event_id}/activate", response_model=EventResponseSchema)
def activate_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    return EventController.change_status(db, event_id, True, user)

@router.patch("/events/{event_id}/deactivate", response_model=EventResponseSchema)
def deactivate_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    return EventController.change_status(db, event_id, False, user)

@router.patch("/events/{event_id}/post-approval", response_model=EventResponseSchema)
def update_post_approval_requirement(
    event_id: int,
    requires_approval: bool = Query(...),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):
    """
    Atualiza se o evento requer aprovação de posts.
    Se desativar a aprovação e houver posts pendentes, eles serão aprovados automaticamente.
    """
    try:
        result = EventController.update_post_approval_requirement(db, event_id, requires_approval, user)
        return result["event"]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/events/{event_id}/pending-posts-count")
def get_pending_posts_count(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):
    """Retorna a quantidade de posts pendentes de um evento"""
    from app.domain.admin.repositories.news_repository import NewsRepository
    count = NewsRepository.count_pending_by_event(db, event_id)
    return {"event_id": event_id, "pending_count": count}
