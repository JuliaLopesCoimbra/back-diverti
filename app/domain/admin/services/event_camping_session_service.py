from datetime import date, timedelta

from app.domain.admin.repositories.event_camping_area_repository import EventCampingAreaRepository
from app.domain.admin.repositories.event_camping_booking_repository import EventCampingBookingRepository
from app.domain.admin.repositories.event_camping_entry_repository import EventCampingEntryRepository
from app.domain.admin.repositories.event_camping_session_repository import EventCampingSessionRepository


class EventCampingSessionService:
    @staticmethod
    def _serialize_with_metrics(db, session, quantity_bookings=None, quantity_entries=None):
        if quantity_bookings is None:
            quantity_bookings = EventCampingBookingRepository.count_active_by_session(db, session.id)
        if quantity_entries is None:
            quantity_entries = EventCampingEntryRepository.count_by_session(db, session.id)
        quantity_missing_checkins = max(0, quantity_bookings - quantity_entries)
        quantity_remaining_slots = max(0, session.capacity - quantity_bookings)

        return {
            "id": session.id,
            "area_id": session.area_id,
            "label": session.label,
            "check_in_date": session.check_in_date,
            "check_out_date": session.check_out_date,
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
    def create_session(db, area_id: int, data: dict, user):
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise ValueError("Area de camping nao encontrada")

        if data["capacity"] <= 0:
            raise ValueError("A capacidade deve ser maior que zero")

        if data.get("status") and data["status"] not in ["active", "inactive"]:
            raise ValueError("Status invalido. Use 'active' ou 'inactive'")

        if data["check_in_date"] > data["check_out_date"]:
            raise ValueError("A data de check-in deve ser anterior ou igual ao check-out")

        data["area_id"] = area_id
        data["created_by_id"] = user.id
        session = EventCampingSessionRepository.create(db, data)
        return EventCampingSessionService._serialize_with_metrics(db, session)

    @staticmethod
    def get_sessions_by_area(db, area_id: int):
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise ValueError("Area de camping nao encontrada")

        sessions = EventCampingSessionRepository.get_by_area(db, area_id)
        session_ids = [s.id for s in sessions]
        booking_counts = EventCampingBookingRepository.count_active_grouped_by_session(db, session_ids)
        entry_counts = EventCampingEntryRepository.count_grouped_by_session(db, session_ids)

        return [
            EventCampingSessionService._serialize_with_metrics(
                db,
                session,
                quantity_bookings=booking_counts.get(session.id, 0),
                quantity_entries=entry_counts.get(session.id, 0),
            )
            for session in sessions
        ]

    @staticmethod
    def get_session_by_id(db, session_id: int):
        session = EventCampingSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao de camping nao encontrada")
        return EventCampingSessionService._serialize_with_metrics(db, session)

    @staticmethod
    def update_session(db, session_id: int, data: dict, user):
        session = EventCampingSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao de camping nao encontrada")

        if "capacity" in data and data["capacity"] is not None and data["capacity"] <= 0:
            raise ValueError("A capacidade deve ser maior que zero")

        if "status" in data and data["status"] is not None and data["status"] not in ["active", "inactive"]:
            raise ValueError("Status invalido. Use 'active' ou 'inactive'")

        check_in = data.get("check_in_date") or session.check_in_date
        check_out = data.get("check_out_date") or session.check_out_date
        if check_in > check_out:
            raise ValueError("A data de check-in deve ser anterior ou igual ao check-out")

        data["updated_by_id"] = user.id
        updated = EventCampingSessionRepository.update(db, session, data)
        return EventCampingSessionService._serialize_with_metrics(db, updated)

    @staticmethod
    def generate_daily_sessions(db, event_id: int, start_date: date, end_date: date, capacity: int, user) -> dict:
        areas = EventCampingAreaRepository.get_by_event(db, event_id)
        if not areas:
            raise ValueError("Nenhuma área de camping encontrada para este evento")

        created = 0
        skipped = 0

        for area in areas:
            existing = EventCampingSessionRepository.get_by_area(db, area.id)
            existing_dates = {s.check_in_date for s in existing}

            current = start_date
            while current <= end_date:
                if current in existing_dates:
                    skipped += 1
                else:
                    EventCampingSessionRepository.create(db, {
                        "area_id": area.id,
                        "label": current.strftime("%d/%m/%Y"),
                        "check_in_date": current,
                        "check_out_date": current,
                        "capacity": capacity,
                        "status": "active",
                        "created_by_id": user.id,
                    })
                    created += 1
                current += timedelta(days=1)

        return {"created": created, "skipped": skipped, "areas": len(areas)}

    @staticmethod
    def delete_session(db, session_id: int, user):
        session = EventCampingSessionRepository.get(db, session_id)
        if not session:
            raise ValueError("Sessao de camping nao encontrada")
        EventCampingSessionRepository.soft_delete(db, session, user.id)
