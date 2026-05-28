import random
from fastapi import HTTPException
from app.domain.roulette.repositories.spin_repository import SpinRepository
from app.domain.roulette.repositories.prize_repository import PrizeRepository
from app.domain.roulette.repositories.roulette_repository import RouletteRepository

class SpinService:

    @staticmethod
    def spin(db, user_id: int, event_id: int):
        # force_db=True para garantir objeto SQLAlchemy válido (pode precisar para operações)
        roulette = RouletteRepository.get_by_event(db, event_id, force_db=True)

        if not roulette or not roulette.is_active:
            raise HTTPException(404, "Roleta indisponível")

        spins_count = SpinRepository.count_user_spins(db, user_id, event_id)

        prizes = PrizeRepository.list_by_event(db, event_id)

        if not prizes:
            raise HTTPException(404, "Nenhum prêmio configurado")

        weighted_pool = []
        for prize in prizes:
            weighted_pool.extend([prize] * prize.probability)

        chosen_prize = random.choice(weighted_pool)

        spin = SpinRepository.create(db, {
            "user_id": user_id,
            "event_id": event_id,
            "prize_id": chosen_prize.id
        })

        return {
            "spin_id": spin.id,
            "event_id": event_id,

            "prize": {
                "id": chosen_prize.id,
                "name": chosen_prize.name,
                "image_url": chosen_prize.image_url,
                "position": chosen_prize.position

            }
        }
