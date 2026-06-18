from app.domain.roulette.services.roulette_service import RouletteService
from fastapi import HTTPException

class RouletteController:

    @staticmethod
    def create(db, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise HTTPException(403, "Apenas admin master ou admin podem criar roleta")

        return RouletteService.create_roulette(db, data)

    @staticmethod
    def get(db, event_id: int):
        return RouletteService.get_by_event(db, event_id)
