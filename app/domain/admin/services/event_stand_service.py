from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.repositories.event_stand_repository import EventStandRepository


class EventStandService:
    @staticmethod
    def create_stand(db, data: dict, user):
        event = EventRepository.get_by_id(db, data["event_id"], force_db=True)
        if not event:
            raise ValueError("Evento nao encontrado")

        data["created_by_id"] = user.id
        return EventStandRepository.create(db, data)

    @staticmethod
    def get_stands_by_event(db, event_id: int):
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento nao encontrado")

        return EventStandRepository.get_by_event(db, event_id)

    @staticmethod
    def get_stand_by_id(db, stand_id: int):
        stand = EventStandRepository.get(db, stand_id)
        if not stand:
            raise ValueError("Estande nao encontrado")
        return stand

    @staticmethod
    def update_stand(db, stand_id: int, data: dict, user):
        stand = EventStandRepository.get(db, stand_id)
        if not stand:
            raise ValueError("Estande nao encontrado")

        data["updated_by_id"] = user.id
        return EventStandRepository.update(db, stand, data)

    @staticmethod
    def delete_stand(db, stand_id: int, user):
        stand = EventStandRepository.get(db, stand_id)
        if not stand:
            raise ValueError("Estande nao encontrado")

        return EventStandRepository.soft_delete(db, stand, user.id)
