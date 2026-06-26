from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.admin.repositories.event_camping_area_repository import EventCampingAreaRepository
from app.domain.admin.repositories.event_camping_booking_repository import EventCampingBookingRepository
from app.domain.admin.repositories.event_camping_entry_repository import EventCampingEntryRepository
from app.domain.admin.repositories.event_camping_session_repository import EventCampingSessionRepository
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_camping_booking_schema import (
    AdminCampingSessionBookingResponseSchema,
    CampingBookingResponseSchema,
    UserCampingAreaSchema,
    UserCampingSessionSummarySchema,
)
from app.domain.users.services.event_camping_token_service import (
    create_camping_booking_token,
    read_camping_booking_token,
)


class EventCampingBookingService:
    @staticmethod
    def list_camping_areas_for_user(db: Session, event_id: int, user_id: int) -> list[UserCampingAreaSchema]:
        areas = EventCampingAreaRepository.get_by_event(db, event_id)
        if not areas:
            return []

        area_ids = [area.id for area in areas]
        all_sessions = EventCampingSessionRepository.get_by_area_ids(db, area_ids)
        active_sessions = [s for s in all_sessions if s.status == "active"]
        session_ids = [s.id for s in active_sessions]

        booked_slots_by_session = EventCampingBookingRepository.count_active_grouped_by_session(db, session_ids)
        booked_session_ids_by_user = EventCampingBookingRepository.list_active_session_ids_by_user(
            db, user_id, session_ids
        )

        sessions_by_area: dict[int, list[UserCampingSessionSummarySchema]] = {area_id: [] for area_id in area_ids}

        for session in active_sessions:
            booked_slots = booked_slots_by_session.get(session.id, 0)
            remaining_slots = max(session.capacity - booked_slots, 0)
            sessions_by_area.setdefault(session.area_id, []).append(
                UserCampingSessionSummarySchema(
                    id=session.id,
                    area_id=session.area_id,
                    label=session.label,
                    check_in_date=session.check_in_date,
                    check_out_date=session.check_out_date,
                    capacity=session.capacity,
                    status=session.status,
                    booked_slots=booked_slots,
                    remaining_slots=remaining_slots,
                    is_booked=session.id in booked_session_ids_by_user,
                )
            )

        return [
            UserCampingAreaSchema(
                id=area.id,
                event_id=area.event_id,
                name=area.name,
                description=area.description,
                image_url=area.image_url,
                total_spots=area.total_spots,
                x_position=getattr(area, "x_position", None),
                y_position=getattr(area, "y_position", None),
                sessions=sessions_by_area.get(area.id, []),
            )
            for area in areas
        ]

    @staticmethod
    def create_booking(db: Session, camping_session_id: int, user) -> CampingBookingResponseSchema:
        session = EventCampingSessionRepository.get(db, camping_session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao de camping nao encontrada")

        area = EventCampingAreaRepository.get(db, session.area_id)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Area de camping nao encontrada")

        if session.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta sessao nao esta ativa")

        existing = EventCampingBookingRepository.get_active_by_user_and_session(db, user.id, camping_session_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Voce ja possui uma reserva nesta sessao de camping",
            )

        booked_slots = EventCampingBookingRepository.count_active_by_session(db, camping_session_id)
        if booked_slots >= session.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nao ha mais vagas disponiveis para esta sessao",
            )

        booking = EventCampingBookingRepository.create(
            db,
            {"camping_session_id": camping_session_id, "user_id": user.id},
        )
        booking = EventCampingBookingRepository.get(db, booking.id)
        return EventCampingBookingService._to_response(db, booking)

    @staticmethod
    def list_my_bookings(db: Session, user_id: int) -> list[CampingBookingResponseSchema]:
        bookings = EventCampingBookingRepository.list_active_by_user(db, user_id)
        return [EventCampingBookingService._to_response(db, booking) for booking in bookings]

    @staticmethod
    def list_session_bookings(
        admin_db: Session, auth_db: Session, camping_session_id: int
    ) -> list[AdminCampingSessionBookingResponseSchema]:
        bookings = EventCampingBookingRepository.list_active_by_session(admin_db, camping_session_id)
        user_ids = [b.user_id for b in bookings]
        users = {}
        if user_ids:
            users = {u.id: u for u in auth_db.query(User).filter(User.id.in_(user_ids)).all()}

        items = []
        for booking in bookings:
            user = users.get(booking.user_id)
            entry = EventCampingEntryRepository.get_by_booking(admin_db, booking.id)
            items.append(
                AdminCampingSessionBookingResponseSchema(
                    id=booking.id,
                    user_id=booking.user_id,
                    user_name=user.name if user and user.name else "Usuario",
                    user_email=user.email if user else "",
                    user_cpf=user.cpf if user else None,
                    user_profile_photo=user.profile_photo if user else None,
                    created_at=booking.created_at,
                    checked_in_at=entry.created_at if entry else None,
                    checked_in_by_admin_id=entry.admin_id if entry else None,
                )
            )
        return items

    @staticmethod
    def check_in_booking(admin_db: Session, booking_id: int, admin_user) -> AdminCampingSessionBookingResponseSchema:
        booking = EventCampingBookingRepository.get(admin_db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")

        existing_entry = EventCampingEntryRepository.get_by_booking(admin_db, booking_id)
        if existing_entry:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entrada ja registrada")

        EventCampingEntryRepository.create(admin_db, booking_id, admin_user.id)
        entry = EventCampingEntryRepository.get_by_booking(admin_db, booking_id)
        return AdminCampingSessionBookingResponseSchema(
            id=booking.id,
            user_id=booking.user_id,
            user_name="",
            user_email="",
            created_at=booking.created_at,
            checked_in_at=entry.created_at,
            checked_in_by_admin_id=admin_user.id,
        )

    @staticmethod
    def check_in_by_token(admin_db: Session, token: str, admin_user):
        payload = read_camping_booking_token(token)
        if not payload or not payload.get("b"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de QR invalido")

        booking_id = int(payload["b"])
        booking = EventCampingBookingRepository.get(admin_db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")

        existing_entry = EventCampingEntryRepository.get_by_booking(admin_db, booking_id)
        if existing_entry:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entrada ja registrada")

        EventCampingEntryRepository.create(admin_db, booking_id, admin_user.id)
        return {"message": "Entrada registrada com sucesso", "booking_id": booking_id}

    @staticmethod
    def book_area_for_day(db: Session, area_id: int, booking_date: date, user) -> "CampingBookingResponseSchema":
        area = EventCampingAreaRepository.get(db, area_id)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área de camping não encontrada")

        existing_sessions = EventCampingSessionRepository.get_by_area(db, area_id)
        session = next((s for s in existing_sessions if s.check_in_date == booking_date), None)

        if not session:
            session = EventCampingSessionRepository.create(db, {
                "area_id": area_id,
                "label": booking_date.strftime("%d/%m/%Y"),
                "check_in_date": booking_date,
                "check_out_date": booking_date,
                "capacity": 1,
                "status": "active",
                "created_by_id": user.id,
            })

        if session.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta vaga não está disponível neste dia")

        existing_booking = EventCampingBookingRepository.get_active_by_user_and_session(db, user.id, session.id)
        if existing_booking:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Você já possui uma reserva para esta vaga neste dia")

        booked_slots = EventCampingBookingRepository.count_active_by_session(db, session.id)
        if booked_slots >= session.capacity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Não há mais vagas disponíveis para este dia")

        booking = EventCampingBookingRepository.create(db, {"camping_session_id": session.id, "user_id": user.id})
        booking = EventCampingBookingRepository.get(db, booking.id)
        return EventCampingBookingService._to_response(db, booking)

    @staticmethod
    def cancel_booking(db: Session, booking_id: int, user):
        booking = EventCampingBookingRepository.get(db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva nao encontrada")

        if booking.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode cancelar esta reserva")

        EventCampingBookingRepository.cancel_by_user(db, booking, user.id)

    @staticmethod
    def _to_response(db: Session, booking) -> CampingBookingResponseSchema:
        area = booking.session.area
        event = area.event
        entry = EventCampingEntryRepository.get_by_booking(db, booking.id)
        return CampingBookingResponseSchema(
            id=booking.id,
            user_id=booking.user_id,
            camping_session_id=booking.camping_session_id,
            created_at=booking.created_at,
            cancelled_at=booking.cancelled_at,
            checked_in_at=entry.created_at if entry else None,
            checked_in_by_admin_id=entry.admin_id if entry else None,
            area_id=area.id,
            area_name=area.name,
            area_image_url=area.image_url,
            event_id=area.event_id,
            event_title=event.title if event else None,
            label=booking.session.label,
            check_in_date=booking.session.check_in_date,
            check_out_date=booking.session.check_out_date,
            status=booking.session.status,
            qr_token=create_camping_booking_token(booking.id, booking.user_id, booking.camping_session_id),
        )
