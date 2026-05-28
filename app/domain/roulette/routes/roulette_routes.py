from fastapi import APIRouter, Depends,File, UploadFile, Form
from app.config.roulette_db import get_roulette_db
from app.domain.roulette.controllers.roulette_controller import RouletteController
from app.domain.roulette.schemas.roulette_schema import RouletteCreateSchema, RouletteResponseSchema
from app.domain.auth.controllers.auth_controller import get_current_user
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/roulette/events", tags=["Roulette"])

@router.post("/{event_id}")
def create_roulette(
    event_id: int,
    name: str = Form(...),
    roulette_image: UploadFile = File(None),
    pointer_image: UploadFile = File(None),
    db=Depends(get_roulette_db),
    user: User = Depends(get_current_user)
):
    roulette_image_url = (
        upload_image_to_s3(roulette_image, "roulette_photos")
        if roulette_image else None
    )

    pointer_image_url = (
        upload_image_to_s3(pointer_image, "pointer_photos")
        if pointer_image else None
    )

    data = {
        "event_id": event_id,
        "name": name,
        "roulette_image_url": roulette_image_url,
        "pointer_image_url": pointer_image_url
    }

    return RouletteController.create(db, data, user)

@router.get("/{event_id}", response_model=RouletteResponseSchema)
def get_roulette(
    event_id: int,
    db=Depends(get_roulette_db)
):
    roulette = RouletteController.get(db, event_id)
    # Se veio do cache como dict, converter diretamente
    # Se for objeto SQLAlchemy, o Pydantic converterá automaticamente
    if isinstance(roulette, dict):
        return RouletteResponseSchema(**roulette)
    else:
        return RouletteResponseSchema.model_validate(roulette)
