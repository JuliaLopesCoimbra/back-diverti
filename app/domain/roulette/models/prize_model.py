from sqlalchemy import Column, Integer, String, Boolean
from app.config.roulette_db import RouletteBase
from sqlalchemy import UniqueConstraint

class Prize(RouletteBase):
    __tablename__ = "prizes"
    __table_args__ = (
        UniqueConstraint("event_id", "position", name="uq_event_position"),
    )

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, nullable=False)  # admin_db

    name = Column(String, nullable=False)

    probability = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
