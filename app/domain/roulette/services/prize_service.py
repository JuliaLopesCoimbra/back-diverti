from fastapi import HTTPException
from app.domain.roulette.repositories.prize_repository import PrizeRepository
from app.domain.admin.repositories.event_repository import EventRepository
from app.infra.redis import redis_client, CacheKeys

class PrizeService:

    @staticmethod
    def create_prize(db, admin_db, data: dict):
        # 🔒 valida se o evento existe
        event = EventRepository.get_by_id(admin_db, data["event_id"])
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail="Evento não encontrado"
            )
        
        # 🔒 valida posição única por evento
        existing = PrizeRepository.get_by_event_and_position(
            db,
            data["event_id"],
            data["position"]
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Já existe um prêmio nesta posição da roleta"
            )

        result = PrizeRepository.create(db, data)
        
        # Invalida cache de prêmios do evento
        redis_client.delete(CacheKeys.prizes_event(data["event_id"]))
        
        return result

    @staticmethod
    def _prize_to_dict(prize) -> dict:
        """Converte objeto SQLAlchemy Prize para dict serializável"""
        return {
            "id": prize.id,
            "event_id": prize.event_id,
            "name": prize.name,
            "probability": prize.probability,
            "position": prize.position,
            "image_url": prize.image_url,
            "is_active": prize.is_active
        }

    @staticmethod
    def list_prizes(db, event_id: int, limit: int = 50, offset: int = 0):
        """Lista prêmios de um evento com paginação obrigatória"""
        # Cache apenas para primeira página
        if offset == 0:
            cache_key = CacheKeys.prizes_event(event_id)
            cached = redis_client.get(cache_key)
            if cached:
                # cached é uma lista de dicts, retorna o slice solicitado
                return cached[offset:offset + limit]
        
        prizes = PrizeRepository.list_by_event(db, event_id, limit, offset)

        if not prizes and offset == 0:
            raise HTTPException(404, "Nenhum prêmio encontrado")

        # Cacheia apenas primeira página por 10 minutos
        if offset == 0:
            # Converte lista de objetos SQLAlchemy para lista de dicts
            prizes_dict = [PrizeService._prize_to_dict(prize) for prize in prizes]
            cache_key = CacheKeys.prizes_event(event_id)
            redis_client.set(cache_key, prizes_dict, ttl=600)
        
        return prizes
