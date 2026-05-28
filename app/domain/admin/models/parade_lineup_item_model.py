# app/domain/admin/models/parade_lineup_item_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.config.admin_db import AdminBase

class ParadeLineupItem(AdminBase):
    __tablename__ = "parade_lineup_items"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    samba_school_id = Column(Integer, ForeignKey("samba_schools.id", ondelete="CASCADE"), nullable=False, index=True)
    performance_time = Column(Time, nullable=False)
    performance_end_time = Column(Time, nullable=True)
    event_date = Column(Date, nullable=True)
    display_order = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    
    # Campos de auditoria
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    updated_by_id = Column(Integer, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)

    event = relationship("Event", backref="parade_lineup_items")
    samba_school = relationship("SambaSchool", backref="parade_lineup_items")




