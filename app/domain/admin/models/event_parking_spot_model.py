from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventParkingSpot(AdminBase):
    __tablename__ = "event_parking_spots"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(50), nullable=False)
    x_position = Column(Float, nullable=True)
    y_position = Column(Float, nullable=True)
    capacity = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="parking_spots")
    bookings = relationship("ParkingBooking", backref="spot")
