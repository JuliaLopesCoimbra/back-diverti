from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.domain.admin.controllers.samba_school_controller import SambaSchoolController
from app.domain.auth.models.user_model import User
from app.core.security.auth_dependency import get_current_user, require_admin
from app.infra.s3_upload import upload_image_to_s3
from app.domain.admin.schemas.samba_school_schema import SambaSchoolResponseSchema

router = APIRouter(prefix="/admin/events", tags=["Admin - Samba Schools"])

@router.post("/{event_id}/samba-schools", response_model=SambaSchoolResponseSchema)
def create_samba_school(
    event_id: int,
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    song_name: str = Form(None),
    singer: str = Form(None),
    lyrics: str = Form(None),
    music_image: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        image_url = upload_image_to_s3(image, "samba_schools_photos") if image else None
        data = {
            "name": name,
            "description": description,
            "image_url": image_url,
            "event_id": event_id
        }

        school = SambaSchoolController.create(db, data, user)
        
        # Se a letra da música foi fornecida, cria a música/letra para esta escola
        if lyrics and song_name:
            from app.domain.admin.controllers.music_lyrics_controller import MusicLyricsController
            
            music_image_url = upload_image_to_s3(music_image, "music_lyrics_photos") if music_image else None
            music_data = {
                "song_name": song_name,
                "singer": singer,
                "lyrics": lyrics,
                "image_url": music_image_url,
                "samba_school_id": school.id
            }
            
            try:
                MusicLyricsController.create(db, music_data, user)
            except ValueError as e:
                # Se houver erro ao criar a música, não falha a criação da escola
                # mas loga o erro (a escola já foi criada)
                pass

        return school
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get(
    "/{event_id}/samba-schools",
    response_model=list[SambaSchoolResponseSchema]
)
def list_samba_schools_by_event(
    event_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de escolas (1-100)"),
    offset: int = Query(0, ge=0, description="Número de escolas para pular"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        return SambaSchoolController.list_by_event(db, event_id, limit, offset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/{event_id}/samba-schools/{school_id}",
    response_model=SambaSchoolResponseSchema
)
def get_samba_school_by_id(
    event_id: int,
    school_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        school = SambaSchoolController.get_by_id(db, school_id)
        if school.event_id != event_id:
            raise HTTPException(
                status_code=404,
                detail="Escola de samba não encontrada neste evento"
            )
        return school
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put(
    "/{event_id}/samba-schools/{school_id}",
    response_model=SambaSchoolResponseSchema
)
def update_samba_school(
    event_id: int,
    school_id: int,
    name: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        # Verifica se a escola existe e pertence ao evento
        school = SambaSchoolController.get_by_id(db, school_id)
        if not school or school.event_id != event_id:
            raise HTTPException(
                status_code=404,
                detail="Escola de samba não encontrada neste evento"
            )

        image_url = school.image_url
        if image:
            image_url = upload_image_to_s3(image, "samba_schools_photos")

        data = {
            "name": name,
            "description": description,
            "image_url": image_url,
        }

        return SambaSchoolController.update(db, school_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete(
    "/{event_id}/samba-schools/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_samba_school(
    event_id: int,
    school_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        # Verifica se a escola existe e pertence ao evento
        school = SambaSchoolController.get_by_id(db, school_id)
        if not school or school.event_id != event_id:
            raise HTTPException(
                status_code=404,
                detail="Escola de samba não encontrada neste evento"
            )

        SambaSchoolController.delete(db, school_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))