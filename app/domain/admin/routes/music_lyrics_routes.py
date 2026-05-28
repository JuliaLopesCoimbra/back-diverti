from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.admin_db import get_admin_db
from app.domain.admin.controllers.music_lyrics_controller import MusicLyricsController
from app.domain.auth.models.user_model import User
from app.core.security.auth_dependency import get_current_user, require_admin
from app.infra.s3_upload import upload_image_to_s3
from app.domain.admin.schemas.music_lyrics_schema import MusicLyricsResponseSchema

router = APIRouter(prefix="/admin", tags=["Admin - Music Lyrics"])

@router.post("/samba-schools/{samba_school_id}/music-lyrics", response_model=MusicLyricsResponseSchema)
def create_music_lyrics(
    samba_school_id: int,
    song_name: str = Form(...),
    singer: str = Form(None),
    lyrics: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        image_url = upload_image_to_s3(image, "music_lyrics_photos") if image else None
        data = {
            "song_name": song_name,
            "singer": singer,
            "lyrics": lyrics,
            "image_url": image_url,
            "samba_school_id": samba_school_id
        }

        return MusicLyricsController.create(db, data, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get(
    "/samba-schools/{samba_school_id}/music-lyrics",
    response_model=Optional[MusicLyricsResponseSchema]
)
def get_music_lyrics_by_samba_school(
    samba_school_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        return MusicLyricsController.get_by_samba_school(db, samba_school_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/events/{event_id}/music-lyrics",
    response_model=list[MusicLyricsResponseSchema]
)
def list_music_lyrics_by_event(
    event_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de letras (1-100)"),
    offset: int = Query(0, ge=0, description="Número de letras para pular"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        return MusicLyricsController.list_by_event(db, event_id, limit, offset)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/samba-schools/{samba_school_id}/music-lyrics/{music_id}",
    response_model=MusicLyricsResponseSchema
)
def get_music_lyrics_by_id(
    samba_school_id: int,
    music_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    try:
        music = MusicLyricsController.get_by_id(db, music_id)
        if music.samba_school_id != samba_school_id:
            raise HTTPException(
                status_code=404,
                detail="Música/Letra não encontrada nesta escola de samba"
            )
        return music
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put(
    "/samba-schools/{samba_school_id}/music-lyrics/{music_id}",
    response_model=MusicLyricsResponseSchema
)
def update_music_lyrics(
    samba_school_id: int,
    music_id: int,
    song_name: str = Form(...),
    singer: str = Form(None),
    lyrics: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        # Verifica se a música existe e pertence à escola de samba
        music = MusicLyricsController.get_by_id(db, music_id)
        if not music or music.samba_school_id != samba_school_id:
            raise HTTPException(
                status_code=404,
                detail="Música/Letra não encontrada nesta escola de samba"
            )

        image_url = music.image_url
        if image:
            image_url = upload_image_to_s3(image, "music_lyrics_photos")

        data = {
            "song_name": song_name,
            "singer": singer,
            "lyrics": lyrics,
            "image_url": image_url,
        }

        return MusicLyricsController.update(db, music_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.delete(
    "/samba-schools/{samba_school_id}/music-lyrics/{music_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_music_lyrics(
    samba_school_id: int,
    music_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin)
):

    try:
        # Verifica se a música existe e pertence à escola de samba
        music = MusicLyricsController.get_by_id(db, music_id)
        if not music or music.samba_school_id != samba_school_id:
            raise HTTPException(
                status_code=404,
                detail="Música/Letra não encontrada nesta escola de samba"
            )

        MusicLyricsController.delete(db, music_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))