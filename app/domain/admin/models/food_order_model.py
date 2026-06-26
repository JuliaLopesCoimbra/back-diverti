from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase

# Status flow: pending → preparing → ready → delivered


class FoodOrder(AdminBase):
    __tablename__ = "food_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, nullable=False, index=True)
    delivery_spot = Column(String(100), nullable=True)  # camping area name
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending/preparing/ready/delivered/cancelled
    total = Column(Numeric(10, 2), nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("FoodOrderItem", back_populates="order", cascade="all, delete-orphan")
