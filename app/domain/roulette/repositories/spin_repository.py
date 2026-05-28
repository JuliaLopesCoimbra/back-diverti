from sqlalchemy.orm import Session
from app.domain.roulette.models.spin_model import Spin

class SpinRepository:

    @staticmethod
    def create(db: Session, data: dict):
        spin = Spin(**data)
        db.add(spin)
        db.commit()
        db.refresh(spin)
        return spin

    @staticmethod
    def count_user_spins(db, user_id: int, event_id: int):
        return db.query(Spin).filter(
            Spin.user_id == user_id,
            Spin.event_id == event_id
        ).count()
