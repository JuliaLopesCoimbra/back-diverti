from app.domain.admin.repositories.event_camping_area_repository import EventCampingAreaRepository


class EventCampingAreaService:
    @staticmethod
    def create_area(db, data: dict, user):
        data["created_by_id"] = user.id
        return EventCampingAreaRepository.create(db, data)

    @staticmethod
    def get_areas_by_event(db, event_id: int):
        return EventCampingAreaRepository.get_by_event(db, event_id)

    @staticmethod
    def get_area_by_id(db, area_id: int):
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise ValueError("Area de camping nao encontrada")
        return area

    @staticmethod
    def update_area(db, area_id: int, data: dict, user):
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise ValueError("Area de camping nao encontrada")
        data["updated_by_id"] = user.id
        return EventCampingAreaRepository.update(db, area, data)

    @staticmethod
    def delete_area(db, area_id: int, user):
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise ValueError("Area de camping nao encontrada")
        EventCampingAreaRepository.soft_delete(db, area, user.id)
