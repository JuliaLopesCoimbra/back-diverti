from sqlalchemy.orm import Session
from app.domain.roulette.models.roulette_model import Roulette
from app.infra.redis import redis_client, CacheKeys

class RouletteRepository:

    @staticmethod
    def _roulette_to_dict(roulette: Roulette) -> dict:
        """Converte objeto SQLAlchemy Roulette para dict serializável"""
        return {
            "id": roulette.id,
            "event_id": roulette.event_id,
            "name": roulette.name,
            "is_active": roulette.is_active,
            "roulette_image_url": roulette.roulette_image_url,
            "pointer_image_url": roulette.pointer_image_url,
            "expires_at": roulette.expires_at
        }

    @staticmethod
    def get_by_event(db: Session, event_id: int, force_db: bool = False):
        """Busca roleta por evento com cache
        
        Args:
            force_db: Se True, sempre busca do banco ignorando cache (útil para operações de escrita)
        """
        # Se force_db=True, sempre busca do banco
        if not force_db:
            cache_key = CacheKeys.roulette_event(event_id)
            cached = redis_client.get(cache_key)
            if cached is not None:
                # Retorna dict do cache (será convertido para schema na rota)
                return cached
        
        result = db.query(Roulette).filter(
            Roulette.event_id == event_id
        ).first()
        
        if result and not force_db:
            # Converte para dict antes de cachear (apenas para leitura)
            roulette_dict = RouletteRepository._roulette_to_dict(result)
            cache_key = CacheKeys.roulette_event(event_id)
            redis_client.set(cache_key, roulette_dict, ttl=900)
        
        return result

    @staticmethod
    def create(db: Session, data: dict):
        roulette = Roulette(**data)
        db.add(roulette)
        db.commit()
        db.refresh(roulette)
        
        # Invalida cache da roleta do evento
        redis_client.delete(CacheKeys.roulette_event(data["event_id"]))
        
        return roulette

    @staticmethod
    def toggle(db: Session, roulette_id: int, active: bool):
        roulette = db.query(Roulette).get(roulette_id)
        roulette.is_active = active
        db.commit()
        
        # Invalida cache da roleta do evento
        if roulette:
            redis_client.delete(CacheKeys.roulette_event(roulette.event_id))
        
        return roulette
