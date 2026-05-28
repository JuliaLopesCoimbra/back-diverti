from sqlalchemy.orm import Session
from app.domain.admin.models.samba_school_model import SambaSchool

class SambaSchoolRepository:

    @staticmethod
    def create(db: Session, data: dict):
        school = SambaSchool(**data)
        db.add(school)
        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def list_by_event(db: Session, event_id: int, include_deleted: bool = False, limit: int = 50, offset: int = 0):
        """Lista escolas de samba de um evento com paginação obrigatória"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        query = db.query(SambaSchool).filter(SambaSchool.event_id == event_id)
        if not include_deleted:
            query = query.filter(SambaSchool.deleted_at.is_(None))
        return query.order_by(SambaSchool.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def get_by_id(db: Session, school_id: int, include_deleted: bool = False):
        query = db.query(SambaSchool).filter(SambaSchool.id == school_id)
        if not include_deleted:
            query = query.filter(SambaSchool.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def update(db: Session, school: SambaSchool, data: dict):
        from datetime import datetime
        
        for key, value in data.items():
            if value is not None:
                setattr(school, key, value)
        
        # Atualiza updated_at automaticamente se não foi fornecido
        if 'updated_at' not in data:
            school.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(school)
        return school

    @staticmethod
    def delete(db: Session, school):
        """Método legado - não usar. Use SambaSchoolService.delete para soft delete."""
        # Este método não deve ser usado mais, mas mantido para compatibilidade
        db.delete(school)
        db.commit()
