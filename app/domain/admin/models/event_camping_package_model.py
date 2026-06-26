from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class EventCampingPackage(AdminBase):
    __tablename__ = "event_camping_packages"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    badge = Column(String(50), nullable=True)
    badge_color = Column(String(100), nullable=True)
    price_cents = Column(Integer, nullable=False, default=0)
    price_label = Column(String(50), nullable=True)
    period = Column(String(255), nullable=True)
    days = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="camping_packages")
