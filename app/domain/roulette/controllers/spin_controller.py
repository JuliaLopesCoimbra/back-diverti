from app.domain.roulette.services.spin_service import SpinService
from app.domain.roulette.repositories.spin_repository import SpinRepository

class SpinController:

    @staticmethod
    def spin(db, user, event_id: int):
        return SpinService.spin(db, user.id, event_id)

    @staticmethod
    def count_user_spins(db, user, event_id: int):
        count = SpinRepository.count_user_spins(db, user.id, event_id)
        return {"count": count}
