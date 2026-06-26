from sqlalchemy.orm import Session
from app.domain.admin.services.plataforma_config_service import PlataformaConfigService
from app.domain.admin.schemas.plataforma_config_schema import PlataformaConfigUpdateRequest


class PlataformaConfigController:

    @staticmethod
    def get(db: Session):
        return PlataformaConfigService.get_config(db)

    @staticmethod
    def update(db: Session, body: PlataformaConfigUpdateRequest):
        fields = body.model_dump(exclude_none=True)
        return PlataformaConfigService.update_config(db, fields)
