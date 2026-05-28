# app/domain/admin/repositories/event_repository.py

from sqlalchemy.orm import Session, joinedload
from app.domain.admin.models.event_model import Event
from app.infra.redis import redis_client, CacheKeys

class EventRepository:

    @staticmethod
    def _event_to_dict(event: Event) -> dict:
        """Converte objeto SQLAlchemy Event para dict serializável"""
        # Converte time para string no formato HH:mm:ss
        def time_to_str(t):
            if t is None:
                return None
            return t.strftime("%H:%M:%S") if hasattr(t, 'strftime') else str(t)
        
        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "banner_image": event.banner_image,
            "image_map": event.image_map,
            "line_up": event.line_up,
            "spotify_playlist_url": event.spotify_playlist_url,
            "starts_at": event.starts_at.isoformat() if event.starts_at else None,
            "ends_at": event.ends_at.isoformat() if event.ends_at else None,
            "event_dates": event.event_dates,
            "van_arrival_time_start": time_to_str(event.van_arrival_time_start),
            "van_arrival_time_end": time_to_str(event.van_arrival_time_end),
            "van_departure_time_start": time_to_str(event.van_departure_time_start),
            "van_departure_time_end": time_to_str(event.van_departure_time_end),
            "meeting_point_location": event.meeting_point_location,
            "meeting_point_schedule": event.meeting_point_schedule,
            "is_active": event.is_active,
            "requires_post_approval": event.requires_post_approval,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "created_by_id": event.created_by_id,
            "updated_at": event.updated_at.isoformat() if event.updated_at else None,
            "updated_by_id": event.updated_by_id,
            "deleted_at": event.deleted_at.isoformat() if event.deleted_at else None,
            "deleted_by_id": event.deleted_by_id,
            "map_images": [
                {
                    "id": img.id,
                    "event_id": img.event_id,
                    "image_url": img.image_url,
                    "image_order": img.image_order,
                    "created_at": img.created_at.isoformat() if img.created_at else None
                }
                for img in (event.map_images if hasattr(event, 'map_images') and event.map_images else [])
            ]
        }

    @staticmethod
    def create(db: Session, data: dict):
        event = Event(**data)
        db.add(event)
        db.commit()
        db.refresh(event)
        
        # Invalida cache de eventos
        redis_client.delete(CacheKeys.events_list())
        redis_client.delete(CacheKeys.event_details(event.id))
        
        return event

    @staticmethod
    def list(db: Session, include_deleted: bool = False, limit: int = 50, offset: int = 0):
        limit = min(limit, 100)  # Máximo de 100 por requisição
        query = db.query(Event).options(joinedload(Event.map_images))
        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))
        return query.order_by(Event.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def get_by_id(db: Session, event_id: int, include_deleted: bool = False, force_db: bool = False):
        """Busca evento por ID com cache (cacheia como dict)
        
        Args:
            force_db: Se True, sempre busca do banco ignorando cache (útil para operações de escrita)
        """
        # Se force_db=True ou include_deleted=True, sempre busca do banco
        if not force_db and not include_deleted:
            cache_key = CacheKeys.event_details(event_id)
            cached = redis_client.get(cache_key)
            if cached is not None:
                # Retorna dict do cache (será convertido para schema na rota)
                return cached
        
        query = db.query(Event).options(joinedload(Event.map_images)).filter(Event.id == event_id)
        if not include_deleted:
            query = query.filter(Event.deleted_at.is_(None))
        result = query.first()
        
        if result and not include_deleted and not force_db:
            # Converte para dict antes de cachear (apenas para leitura)
            event_dict = EventRepository._event_to_dict(result)
            cache_key = CacheKeys.event_details(event_id)
            redis_client.set(cache_key, event_dict, ttl=600)
        
        return result

    @staticmethod
    def update(db: Session, event: Event, data: dict):
        from datetime import datetime
        
        for key, value in data.items():
            if value is not None:
                setattr(event, key, value)
        
        # Atualiza updated_at automaticamente se não foi fornecido
        if 'updated_at' not in data:
            event.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(event)
        
        # Invalida cache de eventos
        redis_client.delete(CacheKeys.events_list())
        redis_client.delete(CacheKeys.event_details(event.id))
        
        return event

    @staticmethod
    def delete(db: Session, event):
        """Método legado - não usar. Use EventService.delete_event para soft delete."""
        # Este método não deve ser usado mais, mas mantido para compatibilidade
        db.delete(event)
        db.commit()

    @staticmethod
    def list_active(db: Session, limit: int = 50, offset: int = 0):
        """Lista eventos ativos com cache e paginação obrigatória"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        
        # Tenta buscar do cache primeiro (cache contém primeira página completa)
        cache_key = CacheKeys.events_list()
        cached = redis_client.get(cache_key)
        if cached is not None:
            # cached é uma lista de dicts, retorna o slice solicitado
            # O FastAPI/Pydantic vai converter automaticamente
            return cached[offset:offset + limit]
        
        # Se não tem cache, busca do banco
        result = db.query(Event).options(joinedload(Event.map_images)).filter(
            Event.is_active == True,
            Event.deleted_at.is_(None)
        ).order_by(Event.created_at.desc()).limit(limit).offset(offset).all()
        
        # Cacheia apenas primeira página por 10 minutos (600 segundos)
        if offset == 0:
            # Converte lista de objetos SQLAlchemy para lista de dicts
            events_dict = [EventRepository._event_to_dict(event) for event in result]
            redis_client.set(cache_key, events_dict, ttl=600)
        
        return result

    @staticmethod
    def set_status(db: Session, event: Event, is_active: bool, user_id: int = None):
        from datetime import datetime
        
        event.is_active = is_active
        event.updated_at = datetime.utcnow()
        if user_id:
            event.updated_by_id = user_id
        
        db.commit()
        db.refresh(event)
        
        # Invalida cache de eventos
        redis_client.delete(CacheKeys.events_list())
        redis_client.delete(CacheKeys.event_details(event.id))
        
        return event