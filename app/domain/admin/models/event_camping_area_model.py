from sqlalchemy import Column, Float, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventCampingArea(AdminBase):
    __tablename__ = "event_camping_areas"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    total_spots = Column(Integer, nullable=False, default=100)
    x_position = Column(Float, nullable=True)
    y_position = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="camping_areas")
    sessions = relationship(
        "EventCampingSession",
        back_populates="area",
        cascade="all, delete-orphan",
        order_by="EventCampingSession.check_in_date",
    )
