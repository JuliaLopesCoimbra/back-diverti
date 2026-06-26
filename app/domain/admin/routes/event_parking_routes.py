from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_admin_or_master
from app.domain.admin.models.event_camping_booking_model import EventCampingBooking
from app.domain.admin.models.event_camping_session_model import EventCampingSession
from app.domain.admin.repositories.event_parking_repository import EventParkingRepository
from app.domain.admin.schemas.event_parking_spot_schema import (
    ParkingMapResponseSchema,
    ParkingSpotCreateSchema,
    ParkingSpotResponseSchema,
    ParkingSpotUpdateSchema,
)
from app.domain.admin.schemas.parking_booking_schema import (
    ParkingBookingCreateSchema,
    ParkingBookingResponseSchema,
)
from app.domain.auth.models.user_model import User

admin_router = APIRouter(prefix="/admin", tags=["Admin - Parking"])
user_router = APIRouter(prefix="/user", tags=["User - Parking"])
public_router = APIRouter(prefix="/public", tags=["Public - Parking"])


class ParkingMapImageBody(BaseModel):
    parking_map_image_url: str


# ── Admin: Spots ────────────────────────────────────────────────────────────

@admin_router.get("/events/{event_id}/parking-spots", response_model=list[ParkingSpotResponseSchema])
def admin_list_spots(
    event_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    return EventParkingRepository.get_spots_by_event(db, event_id)


@admin_router.post("/parking-spots", response_model=ParkingSpotResponseSchema, status_code=status.HTTP_201_CREATED)
def admin_create_spot(
    body: ParkingSpotCreateSchema,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    data = body.model_dump()
    data["created_by_id"] = current_user.id
    return EventParkingRepository.create_spot(db, data)


@admin_router.put("/parking-spots/{spot_id}", response_model=ParkingSpotResponseSchema)
def admin_update_spot(
    spot_id: int,
    body: ParkingSpotUpdateSchema,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    spot = EventParkingRepository.get_spot(db, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    data["updated_by_id"] = current_user.id
    return EventParkingRepository.update_spot(db, spot, data)


@admin_router.delete("/parking-spots/{spot_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_spot(
    spot_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    spot = EventParkingRepository.get_spot(db, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")
    EventParkingRepository.soft_delete_spot(db, spot, current_user.id)


@admin_router.get("/events/{event_id}/parking-bookings", response_model=list[ParkingBookingResponseSchema])
def admin_list_parking_bookings(
    event_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    return EventParkingRepository.get_bookings_by_event(db, event_id)


@admin_router.post("/events/{event_id}/parking/generate-from-camping", response_model=list[ParkingSpotResponseSchema])
def admin_generate_parking_from_camping(
    event_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    from app.domain.admin.models.event_camping_area_model import EventCampingArea

    areas = (
        db.query(EventCampingArea)
        .filter(EventCampingArea.event_id == event_id, EventCampingArea.deleted_at.is_(None))
        .order_by(EventCampingArea.id)
        .all()
    )
    if not areas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma área de camping encontrada para este evento")

    # Soft-delete existing spots
    existing = EventParkingRepository.get_spots_by_event(db, event_id)
    for spot in existing:
        EventParkingRepository.soft_delete_spot(db, spot, current_user.id)

    # Build spot list: 1 per camping area, capacity = total_spots, label from area name
    total_areas = len(areas)
    cols = min(8, total_areas)
    rows_count = (total_areas + cols - 1) // cols

    created = []
    for idx, area in enumerate(areas):
        col = idx % cols
        row = idx // cols
        # Spread evenly on the map (percentage positions)
        x = round(8 + col * (84 / max(cols - 1, 1)) if cols > 1 else 50, 2)
        y = round(20 + row * (60 / max(rows_count - 1, 1)) if rows_count > 1 else 50, 2)
        label = area.name[:6] if len(area.name) > 6 else area.name
        data = {
            "event_id": event_id,
            "label": label,
            "x_position": x,
            "y_position": y,
            "capacity": area.total_spots,
            "is_active": True,
            "sort_order": idx,
            "created_by_id": current_user.id,
        }
        created.append(EventParkingRepository.create_spot(db, data))

    return created


@admin_router.delete("/parking-bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_cancel_parking_booking(
    booking_id: int,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    booking = EventParkingRepository.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    EventParkingRepository.cancel_booking(db, booking, cancelled_by_admin_id=current_user.id)


# ── Admin: Parking map image (stored on events table via ALTER TABLE) ────────

@admin_router.patch("/events/{event_id}/parking-map-image")
def admin_update_parking_map_image(
    event_id: int,
    body: ParkingMapImageBody,
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    from app.domain.admin.models.event_model import Event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")
    event.parking_map_image_url = body.parking_map_image_url
    db.commit()
    return {"parking_map_image_url": event.parking_map_image_url}


@admin_router.patch("/events/{event_id}/parking-map")
def admin_upload_parking_map(
    event_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_admin_db),
    current_user=Depends(require_admin_or_master),
):
    from app.domain.admin.models.event_model import Event
    from app.infra.s3_upload import upload_image_to_s3
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento não encontrado")
    url = upload_image_to_s3(image, folder="parking_maps")
    event.parking_map_image_url = url
    db.commit()
    return {"parking_map_image_url": event.parking_map_image_url}


# ── User: Spots ─────────────────────────────────────────────────────────────

@user_router.get("/events/{event_id}/parking-map", response_model=ParkingMapResponseSchema)
def user_get_parking_map(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    from app.domain.admin.models.event_model import Event
    event = db.query(Event).filter(Event.id == event_id).first()
    image_url = getattr(event, "parking_map_image_url", None) if event else None
    spots = EventParkingRepository.get_active_spots_by_event(db, event_id)
    my_booking = EventParkingRepository.get_my_booking_for_event(db, user.id, event_id)
    for spot in spots:
        spot.is_mine = my_booking is not None and my_booking.parking_spot_id == spot.id
    return {"image_url": image_url, "spots": spots}


# ── User: Bookings ───────────────────────────────────────────────────────────

@user_router.get("/parking-bookings", response_model=list[ParkingBookingResponseSchema])
def user_list_parking_bookings(
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return EventParkingRepository.get_my_bookings(db, user.id)


@user_router.get("/events/{event_id}/parking-booking", response_model=ParkingBookingResponseSchema)
def user_get_parking_booking_for_event(
    event_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    booking = EventParkingRepository.get_my_booking_for_event(db, user.id, event_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sem reserva de estacionamento")
    return booking


@user_router.post("/parking-bookings", response_model=ParkingBookingResponseSchema, status_code=status.HTTP_201_CREATED)
def user_create_parking_booking(
    body: ParkingBookingCreateSchema,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    # Must have at least one active camping booking for this event
    from app.domain.admin.models.event_camping_area_model import EventCampingArea
    has_camping = (
        db.query(EventCampingBooking)
        .join(EventCampingSession, EventCampingBooking.camping_session_id == EventCampingSession.id)
        .join(EventCampingArea, EventCampingSession.area_id == EventCampingArea.id)
        .filter(
            EventCampingBooking.user_id == user.id,
            EventCampingArea.event_id == body.event_id,
            EventCampingBooking.cancelled_at.is_(None),
        )
        .first()
    )
    if not has_camping:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="É necessário ter uma reserva de camping ativa para reservar estacionamento",
        )

    # Only 1 active parking booking per user per event
    existing = EventParkingRepository.get_my_booking_for_event(db, user.id, body.event_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você já tem uma vaga de estacionamento reservada para este evento",
        )

    # Check spot availability
    spot = EventParkingRepository.get_spot(db, body.parking_spot_id)
    if not spot or not spot.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaga não encontrada")

    booked = EventParkingRepository.get_spots_by_event(db, body.event_id)
    target = next((s for s in booked if s.id == body.parking_spot_id), None)
    if target and target.booked_count >= target.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaga já ocupada")

    booking = EventParkingRepository.create_booking(db, {
        "user_id": user.id,
        "event_id": body.event_id,
        "parking_spot_id": body.parking_spot_id,
    })
    return booking


@user_router.delete("/parking-bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def user_cancel_parking_booking(
    booking_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    booking = EventParkingRepository.get_booking(db, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    EventParkingRepository.cancel_booking(db, booking, cancelled_by_user_id=user.id)


# ── Public: Parking map ──────────────────────────────────────────────────────

@public_router.get("/events/{event_id}/parking-map", response_model=ParkingMapResponseSchema)
def public_get_parking_map(
    event_id: int,
    db: Session = Depends(get_admin_db),
):
    from app.domain.admin.models.event_model import Event
    event = db.query(Event).filter(Event.id == event_id).first()
    image_url = getattr(event, "parking_map_image_url", None) if event else None
    spots = EventParkingRepository.get_active_spots_by_event(db, event_id)
    return {"image_url": image_url, "spots": spots}
