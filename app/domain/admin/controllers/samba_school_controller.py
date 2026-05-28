from app.domain.admin.services.samba_school_service import SambaSchoolService

class SambaSchoolController:

    @staticmethod
    def create(db, data, user):
        return SambaSchoolService.create(db, data, user)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        return SambaSchoolService.list_by_event(db, event_id, limit, offset)

    @staticmethod
    def get_by_id(db, school_id: int):
        return SambaSchoolService.get_by_id(db, school_id)

    @staticmethod
    def update(db, school_id: int, data: dict, user):
        return SambaSchoolService.update(db, school_id, data, user)

    @staticmethod
    def delete(db, school_id: int, user):
        return SambaSchoolService.delete(db, school_id, user)