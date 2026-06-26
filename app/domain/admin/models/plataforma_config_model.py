from sqlalchemy import Column, Integer, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase


class PlataformaConfig(AdminBase):
    __tablename__ = "plataforma_config"

    id = Column(Integer, primary_key=True, default=1)

    # Preços
    cpc = Column(Float, nullable=False, default=0.14)
    cpv = Column(Float, nullable=False, default=0.10)

    # Limites de campanha
    min_radius = Column(Float, nullable=False, default=1.0)
    min_duration = Column(Integer, nullable=False, default=3)
    min_units = Column(Integer, nullable=False, default=100)
    max_budget = Column(Float, nullable=False, default=50000.0)

    # Configurações da plataforma
    new_sponsors = Column(Boolean, nullable=False, default=True)
    email_notifications = Column(Boolean, nullable=False, default=True)
    auto_approve = Column(Boolean, nullable=False, default=False)
    maintenance_mode = Column(Boolean, nullable=False, default=False)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
