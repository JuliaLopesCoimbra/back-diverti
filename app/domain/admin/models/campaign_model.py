# app/domain/admin/models/campaign_model.py

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class Campaign(AdminBase):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    patrocinador_id = Column(Integer, nullable=False, index=True)  # references auth_db users.id (sem FK cross-DB)

    # Campaign info
    campaign_name = Column(String(200), nullable=False)
    ad_type = Column(String(10), nullable=False)  # "CPC" or "CPV"
    creative_url = Column(Text, nullable=True)
    creative_name = Column(String(300), nullable=True)
    redirect_url = Column(Text, nullable=True)

    # Event association (optional)
    event_id = Column(Integer, nullable=True, index=True)

    # Budget
    target_units = Column(Integer, nullable=False, default=1000)
    budget_type = Column(String(20), nullable=False, default="total")  # "diario" or "total"
    budget_value = Column(Float, nullable=False, default=0.0)  # calculated total cost
    start_at = Column(DateTime(timezone=True), nullable=True)
    duration_days = Column(Integer, nullable=True, default=7)

    # Segmentation (stored as JSON)
    hobbies = Column(JSON, nullable=True, default=list)
    professions = Column(JSON, nullable=True, default=list)
    gender = Column(String(20), nullable=True, default="todos")
    age_min = Column(Integer, nullable=True, default=18)
    age_max = Column(Integer, nullable=True, default=65)
    address = Column(Text, nullable=True)
    radius_km = Column(Float, nullable=True, default=10.0)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="active")  # active, paused, completed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
