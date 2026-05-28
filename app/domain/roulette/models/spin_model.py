from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from app.config.roulette_db import RouletteBase

class Spin(RouletteBase):
    __tablename__ = "spins"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    prize_id = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
