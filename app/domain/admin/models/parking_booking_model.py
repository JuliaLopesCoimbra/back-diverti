import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


def _gen_token():
    return str(uuid.uuid4()).replace("-", "")


class ParkingBooking(AdminBase):
    __tablename__ = "parking_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    parking_spot_id = Column(Integer, ForeignKey("event_parking_spots.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")
    qr_token = Column(String(64), nullable=False, default=_gen_token)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id = Column(Integer, nullable=True)
    cancelled_by_admin_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="parking_bookings")

    @property
    def spot_label(self):
        return self.spot.label if self.spot else None
