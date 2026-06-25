from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventCampingEntry(AdminBase):
    __tablename__ = "event_camping_entries"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("event_camping_bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    admin_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("EventCampingBooking", backref="entry")
