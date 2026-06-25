from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventCampingBooking(AdminBase):
    __tablename__ = "event_camping_bookings"

    id = Column(Integer, primary_key=True, index=True)
    camping_session_id = Column(Integer, ForeignKey("event_camping_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id = Column(Integer, nullable=True)
    cancelled_by_admin_id = Column(Integer, nullable=True)

    session = relationship("EventCampingSession", backref="bookings")
