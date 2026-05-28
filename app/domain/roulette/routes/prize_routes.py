from fastapi import APIRouter, Depends, Query, File, UploadFile, Form
from app.config.roulette_db import get_roulette_db
from app.config.admin_db import get_admin_db
from app.domain.roulette.controllers.prize_controller import PrizeController
from app.domain.roulette.schemas.prize_schema import PrizeCreateSchema, PrizeResponseSchema
from app.domain.auth.controllers.auth_controller import get_current_user
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/roulette/events", tags=["Prizes"])

@router.post("/{event_id}/prizes")
def create_prize(
    event_id: int,
    name: str = Form(...),
    probability: float = Form(...),
    position: int = Form(...),
    image: UploadFile = File(None),
    db=Depends(get_roulette_db),
    admin_db=Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    image_url = upload_image_to_s3(
        image,
        "prize_photos"
    ) if image else None

    data = {
        "event_id": event_id,
        "name": name,
        "probability": probability,
        "position": position,
        "image_url": image_url
    }

    return PrizeController.create(db, admin_db, data, user)

@router.get("/{event_id}/prizes", response_model=list[PrizeResponseSchema])
def list_prizes(
    event_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de prêmios (1-100)"),
    offset: int = Query(0, ge=0, description="Número de prêmios para pular"),
    db=Depends(get_roulette_db)
):
    prizes = PrizeController.list(db, event_id, limit, offset)
    # Se vier do cache como lista de dicts, converter para schemas
    # Se for lista de objetos SQLAlchemy, o Pydantic converterá automaticamente
    if prizes and len(prizes) > 0 and isinstance(prizes[0], dict):
        return [PrizeResponseSchema(**prize) for prize in prizes]
    return prizes
