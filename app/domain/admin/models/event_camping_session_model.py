from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventCampingSession(AdminBase):
    __tablename__ = "event_camping_sessions"

    id = Column(Integer, primary_key=True, index=True)
    area_id = Column(Integer, ForeignKey("event_camping_areas.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    check_in_date = Column(Date, nullable=False, index=True)
    check_out_date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=False, default=100)
    status = Column(String(20), nullable=False, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    area = relationship("EventCampingArea", back_populates="sessions")
