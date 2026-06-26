from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config.admin_db import AdminBase


class FoodOrderItem(AdminBase):
    __tablename__ = "food_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("food_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, nullable=True)  # nullable so item can be deleted without breaking history
    item_name = Column(String(255), nullable=False)   # snapshot
    unit_price = Column(Numeric(10, 2), nullable=False)  # snapshot
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("FoodOrder", back_populates="items")
