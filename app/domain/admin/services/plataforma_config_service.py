from sqlalchemy.orm import Session
from app.domain.admin.repositories.plataforma_config_repository import PlataformaConfigRepository


class PlataformaConfigService:

    @staticmethod
    def get_config(db: Session):
        return PlataformaConfigRepository.get(db)

    @staticmethod
    def update_config(db: Session, fields: dict):
        return PlataformaConfigRepository.update(db, fields)
