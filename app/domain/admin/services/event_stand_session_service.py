from app.domain.admin.repositories.event_stand_repository import EventStandRepository
from app.domain.admin.repositories.event_stand_booking_repository import EventStandBookingRepository
from app.domain.admin.repositories.event_stand_entry_repository import EventStandEntryRepository
from app.domain.admin.repositories.event_stand_session_repository import EventStandSessionRepository


class EventStandSessionService:
    @staticmethod
    def _serialize_with_metrics(db, session, quantity_bookings=None, quantity_entries=None):
        if quantity_bookings is None:
            quantity_bookings = EventStandBookingRepository.count_active_by_session(db, session.id)
        if quantity_entries is None:
            quantity_entries = EventStandEntryRepository.count_by_session(db, session.id)
        quantity_missing_checkins = max(0, quantity_bookings - quantity_entries)
        quantity_remaining_slots = max(0, session.capacity - quantity_bookings)

        return {
            "id": session.id,
            "stand_id": session.stand_id,
            "session_date": session.session_date,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "booking_open_time": session.booking_open_time,
            "capacity": session.capacity,
            "status": session.status,
            "created_at": session.created_at,
            "created_by_id": session.created_by_id,
            "updated_at": session.updated_at,
            "updated_by_id": session.updated_by_id,
            "deleted_at": session.deleted_at,
            "deleted_by_id": session.deleted_by_id,
            "quantity_bookings": quantity_bookings,
            "quantity_entries": quantity_entries,
            "quantity_missing_checkins": quantity_missing_checkins,
            "quantity_remaining_slots": quantity_remaining_slots,
        }

    @staticmethod
    def create_session(db, stand_id: int, data: dict, user):
        stand = EventStandRepository.get(db, stand_id)
        if not stand:
            raise ValueError("Estande nao encontrado")

        if data["capacity"] <= 0:
            raise ValueError("A capacidade deve ser maior que zero")

        if data.get("status") and data["status"] not in ["active", "inactive"]:
            raise ValueError("Status invalido. Use 'active' ou 'inactive'")

        data["stand_id"] = stand_id
        data["created_by_id"] = user.id
        session = EventStandSessionRepository.create(db, data)
        return EventStandSessionService._serialize_with_metrics(db, session)

    @staticmethod
    def get_sessions_by_stand(db, stand_id: int):
        stand = EventStandRepository.get(db, stand_id)
        if not stand:
            raise ValueError("Estande nao encontrado")

        sessions = EventStandSessionRepository.get_by_stand(db, stand_id)
        session_ids = [session.id for session in sessions]
        booking_counts = EventStandBookingRepository.count_active_grouped_by_session(db, session_ids)
        entry_counts = EventStandEntryRepository.count_grouped_by_session(db, session_ids)

        return [
            EventStandSessionService._serialize_with_metrics(
                db,
                session,
                quantity_bookings=booking_counts.get(session.id, 0),
                quantity_entries=entry_counts.get(session.id, 0),
            )
            for session in sessions
        ]

    @staticmethod
    def get_session_by_id(db, session_id: int):
        session = EventStandSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao nao encontrada")
        return EventStandSessionService._serialize_with_metrics(db, session)

    @staticmethod
    def update_session(db, session_id: int, data: dict, user):
        session = EventStandSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao nao encontrada")

        if "capacity" in data and data["capacity"] is not None and data["capacity"] <= 0:
            raise ValueError("A capacidade deve ser maior que zero")

        if "status" in data and data["status"] is not None and data["status"] not in ["active", "inactive"]:
            raise ValueError("Status invalido. Use 'active' ou 'inactive'")

        data["updated_by_id"] = user.id
        updated_session = EventStandSessionRepository.update(db, session, data)
        return EventStandSessionService._serialize_with_metrics(db, updated_session)

    @staticmethod
    def delete_session(db, session_id: int, user):
        session = EventStandSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao nao encontrada")
        return EventStandSessionRepository.soft_delete(db, session, user.id)
