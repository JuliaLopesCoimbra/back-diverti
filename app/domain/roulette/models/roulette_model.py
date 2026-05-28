from sqlalchemy import Column, Integer, String, Boolean
from app.config.roulette_db import RouletteBase

class Roulette(RouletteBase):
    __tablename__ = "roulettes"

    id = Column(Integer, primary_key=True, index=True)


    event_id = Column(Integer, nullable=False, unique=True)

    name = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)

    roulette_image_url = Column(String, nullable=True)
    pointer_image_url = Column(String, nullable=True)

    expires_at = Column(String, nullable=True)
