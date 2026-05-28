
from sqlalchemy.orm import Session
from app.domain.roulette.models.prize_model import Prize

class PrizeRepository:

    @staticmethod
    def list_by_event(db: Session, event_id: int, limit: int = 50, offset: int = 0):
        """Lista prêmios de um evento com paginação obrigatória"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        return db.query(Prize).filter(
            Prize.event_id == event_id,
            Prize.is_active == True
        ).order_by(Prize.position).limit(limit).offset(offset).all()

    @staticmethod
    def get_by_event_and_position(db: Session, event_id: int, position: int):
        return db.query(Prize).filter(
            Prize.event_id == event_id,
            Prize.position == position,
            Prize.is_active == True
        ).first()

    @staticmethod
    def create(db: Session, data: dict):
        prize = Prize(**data)
        db.add(prize)
        db.commit()
        db.refresh(prize)
        return prize

