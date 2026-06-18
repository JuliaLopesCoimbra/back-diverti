from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.repositories.samba_school_repository import SambaSchoolRepository

class SambaSchoolService:

    @staticmethod
    def create(db, data, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem criar escolas")

        event = EventRepository.get_by_id(db, data["event_id"])
        if not event:
            raise ValueError("Evento não encontrado")
        
        # Adiciona created_by_id ao data
        data["created_by_id"] = user.id
        
        return SambaSchoolRepository.create(db, data)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Evento não encontrado")

        return SambaSchoolRepository.list_by_event(db, event_id, limit=limit, offset=offset)

    @staticmethod
    def get_by_id(db, school_id: int):
        school = SambaSchoolRepository.get_by_id(db, school_id)
        if not school:
            raise ValueError("Escola de samba não encontrada")
        return school

    @staticmethod
    def update(db, school_id: int, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem editar escolas de samba")

        school = SambaSchoolRepository.get_by_id(db, school_id)
        if not school:
            raise ValueError("Escola de samba não encontrada")

        # Remove event_id dos dados se presente (não deve ser alterado)
        data.pop("event_id", None)
        
        # Adiciona updated_by_id ao data
        data["updated_by_id"] = user.id

        return SambaSchoolRepository.update(db, school, data)

    @staticmethod
    def delete(db, school_id: int, user):
        from datetime import datetime
        
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem deletar escolas de samba")

        school = SambaSchoolRepository.get_by_id(db, school_id)
        if not school:
            raise ValueError("Escola de samba não encontrada")

        # Verifica se já foi deletado
        if school.deleted_at is not None:
            raise ValueError("Escola de samba já foi deletada")

        # Soft delete: marca como deletado sem remover do banco
        school.deleted_at = datetime.utcnow()
        school.deleted_by_id = user.id
        
        db.commit()
        db.refresh(school)
        
        return school