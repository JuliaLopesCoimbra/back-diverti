from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.admin.repositories.event_stand_booking_repository import EventStandBookingRepository
from app.domain.admin.repositories.event_stand_entry_repository import EventStandEntryRepository
from app.domain.admin.repositories.event_stand_repository import EventStandRepository
from app.domain.admin.repositories.event_stand_session_repository import EventStandSessionRepository
from app.domain.auth.models.user_model import User
from app.domain.users.schemas.event_stand_booking_schema import (
    AdminStandSessionBookingResponseSchema,
    EventStandBookingResponseSchema,
    StandBookingCheckInByTokenSchema,
    UserEventStandSchema,
    UserStandSessionSummarySchema,
)
from app.domain.users.services.event_stand_token_service import create_stand_booking_token, read_stand_booking_token


class EventStandBookingService:
    @staticmethod
    def list_event_stands_for_user(db: Session, event_id: int, user_id: int) -> list[UserEventStandSchema]:
        stands = EventStandRepository.get_by_event(db, event_id)
        if not stands:
            return []

        stand_ids = [stand.id for stand in stands]
        all_sessions = EventStandSessionRepository.get_by_stand_ids(db, stand_ids)
        active_sessions = [session for session in all_sessions if session.status == "active"]
        session_ids = [session.id for session in active_sessions]

        booked_slots_by_session = EventStandBookingRepository.count_active_grouped_by_session(db, session_ids)
        booked_session_ids_by_user = EventStandBookingRepository.list_active_session_ids_by_user(
            db, user_id, session_ids
        )

        sessions_by_stand: dict[int, list[UserStandSessionSummarySchema]] = {stand_id: [] for stand_id in stand_ids}

        for session in active_sessions:
            booked_slots = booked_slots_by_session.get(session.id, 0)
            remaining_slots = max(session.capacity - booked_slots, 0)

            sessions_by_stand.setdefault(session.stand_id, []).append(
                UserStandSessionSummarySchema(
                    id=session.id,
                    stand_id=session.stand_id,
                    session_date=session.session_date,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    booking_open_time=session.booking_open_time,
                    capacity=session.capacity,
                    status=session.status,
                    booked_slots=booked_slots,
                    remaining_slots=remaining_slots,
                    is_booked=session.id in booked_session_ids_by_user,
                )
            )

        return [
            UserEventStandSchema(
                id=stand.id,
                event_id=stand.event_id,
                name=stand.name,
                image_url=stand.image_url,
                description=stand.description,
                sessions=sessions_by_stand.get(stand.id, []),
            )
            for stand in stands
        ]

    @staticmethod
    def create_booking(db: Session, stand_session_id: int, user) -> EventStandBookingResponseSchema:
        session = EventStandSessionRepository.get(db, stand_session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada")

        stand = EventStandRepository.get(db, session.stand_id)
        if not stand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estande nao encontrado")

        if session.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta sessao nao esta ativa")

        existing_booking = EventStandBookingRepository.get_active_by_user_and_session(db, user.id, stand_session_id)
        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Voce ja possui um agendamento nesta sessao",
            )

        booked_slots = EventStandBookingRepository.count_active_by_session(db, stand_session_id)
        if booked_slots >= session.capacity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nao ha mais vagas disponiveis para esta sessao",
            )

        booking = EventStandBookingRepository.create(
            db,
            {
                "stand_session_id": stand_session_id,
                "user_id": user.id,
            },
        )

        booking = EventStandBookingRepository.get(db, booking.id)
        return EventStandBookingService._to_response(db, booking)

    @staticmethod
    def list_my_bookings(db: Session, user_id: int) -> list[EventStandBookingResponseSchema]:
        bookings = EventStandBookingRepository.list_active_by_user(db, user_id)
        return [EventStandBookingService._to_response(db, booking) for booking in bookings]

    @staticmethod
    def list_session_bookings(admin_db: Session, auth_db: Session, stand_session_id: int) -> list[AdminStandSessionBookingResponseSchema]:
        bookings = EventStandBookingRepository.list_active_by_session(admin_db, stand_session_id)
        user_ids = [booking.user_id for booking in bookings]
        users = {}
        if user_ids:
            users = {user.id: user for user in auth_db.query(User).filter(User.id.in_(user_ids)).all()}

        items = []
        for booking in bookings:
            user = users.get(booking.user_id)
            entry = EventStandEntryRepository.get_by_booking(admin_db, booking.id)
            items.append(
                AdminStandSessionBookingResponseSchema(
                    id=booking.id,
                    user_id=booking.user_id,
                    user_name=user.name if user and user.name else "Usuario",
                    user_email=user.email if user else "",
                    created_at=booking.created_at,
                    checked_in_at=entry.created_at if entry else None,
                    checked_in_by_admin_id=entry.admin_id if entry else None,
                )
            )
        return items

    @staticmethod
    def check_in_booking(admin_db: Session, booking_id: int, admin_user) -> AdminStandSessionBookingResponseSchema:
        booking = EventStandBookingRepository.get(admin_db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento nao encontrado")

        existing_entry = EventStandEntryRepository.get_by_booking(admin_db, booking_id)
        if existing_entry:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entrada ja registrada")

        EventStandEntryRepository.create(admin_db, booking_id, admin_user.id)
        return AdminStandSessionBookingResponseSchema(
            id=booking.id,
            user_id=booking.user_id,
            user_name="",
            user_email="",
            created_at=booking.created_at,
            checked_in_at=EventStandEntryRepository.get_by_booking(admin_db, booking_id).created_at,
            checked_in_by_admin_id=admin_user.id,
        )

    @staticmethod
    def check_in_by_token(admin_db: Session, token: str, admin_user):
        payload = read_stand_booking_token(token)
        if not payload or not payload.get("b"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de QR invalido")

        booking_id = int(payload["b"])
        booking = EventStandBookingRepository.get(admin_db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento nao encontrado")

        existing_entry = EventStandEntryRepository.get_by_booking(admin_db, booking_id)
        if existing_entry:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Entrada ja registrada")

        EventStandEntryRepository.create(admin_db, booking_id, admin_user.id)
        return {"message": "Entrada registrada com sucesso", "booking_id": booking_id}

    @staticmethod
    def cancel_booking(db: Session, booking_id: int, user):
        booking = EventStandBookingRepository.get(db, booking_id)
        if not booking or booking.cancelled_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento nao encontrado")

        if booking.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode cancelar este agendamento")

        EventStandBookingRepository.cancel_by_user(db, booking, user.id)

    @staticmethod
    def _to_response(db: Session, booking) -> EventStandBookingResponseSchema:
        stand = booking.session.stand
        event = stand.event
        entry = EventStandEntryRepository.get_by_booking(db, booking.id)
        return EventStandBookingResponseSchema(
            id=booking.id,
            user_id=booking.user_id,
            stand_session_id=booking.stand_session_id,
            created_at=booking.created_at,
            cancelled_at=booking.cancelled_at,
            checked_in_at=entry.created_at if entry else None,
            checked_in_by_admin_id=entry.admin_id if entry else None,
            stand_id=stand.id,
            stand_name=stand.name,
            stand_image_url=stand.image_url,
            event_id=stand.event_id,
            event_title=event.title if event else None,
            session_date=booking.session.session_date,
            start_time=booking.session.start_time,
            end_time=booking.session.end_time,
            booking_open_time=booking.session.booking_open_time,
            status=booking.session.status,
            qr_token=create_stand_booking_token(booking.id, booking.user_id, booking.stand_session_id),
        )
