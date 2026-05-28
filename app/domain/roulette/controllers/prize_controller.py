from app.domain.roulette.services.prize_service import PrizeService
from fastapi import HTTPException

class PrizeController:

    @staticmethod
    def create(db, admin_db, data: dict, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise HTTPException(
                status_code=403,
                detail="Apenas admin master ou subadmin podem criar prêmios"
            )

        return PrizeService.create_prize(db, admin_db, data)

    @staticmethod
    def list(db, event_id: int, limit: int = 50, offset: int = 0):
        return PrizeService.list_prizes(db, event_id, limit, offset)
