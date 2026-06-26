from sqlalchemy.orm import Session
from app.domain.admin.models.plataforma_config_model import PlataformaConfig


class PlataformaConfigRepository:

    @staticmethod
    def get(db: Session) -> PlataformaConfig:
        config = db.query(PlataformaConfig).filter(PlataformaConfig.id == 1).first()
        if not config:
            config = PlataformaConfig(id=1)
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def update(db: Session, fields: dict) -> PlataformaConfig:
        config = PlataformaConfigRepository.get(db)
        for key, value in fields.items():
            if value is not None:
                setattr(config, key, value)
        db.commit()
        db.refresh(config)
        return config
