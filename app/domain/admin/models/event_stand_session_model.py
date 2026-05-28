from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventStandSession(AdminBase):
    __tablename__ = "event_stand_sessions"

    id = Column(Integer, primary_key=True, index=True)
    stand_id = Column(Integer, ForeignKey("event_stands.id", ondelete="CASCADE"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=True)
    booking_open_time = Column(Time, nullable=True)
    capacity = Column(Integer, nullable=False, default=100)
    status = Column(String(20), nullable=False, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    stand = relationship("EventStand", back_populates="sessions")
