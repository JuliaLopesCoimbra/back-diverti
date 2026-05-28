from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.core.security.auth_dependency import get_current_user, get_current_user_optional
from app.domain.auth.models.user_model import User
from app.domain.users.controllers.profile_controller import ProfileController
from app.domain.users.schemas.profile_schema import ProfileResponse, UpdateProfileRequest
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/user", tags=["Profile"])

@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Retorna os dados do perfil do usuário autenticado"""
    return ProfileController.get_profile(db, user)

@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Atualiza os dados do perfil do usuário autenticado (data de nascimento e/ou sexo)"""
    # Valida se pelo menos um campo foi fornecido
    if body.birth_date is None and body.gender is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pelo menos um campo (birth_date ou gender) deve ser fornecido"
        )
    
    return ProfileController.update_profile(
        db, 
        user, 
        birth_date=body.birth_date,
        gender=body.gender
    )

@router.put("/profile/photo", response_model=ProfileResponse)
def update_profile_photo(
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Atualiza a foto de perfil do usuário autenticado"""
    # Valida se é uma imagem
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser uma imagem"
        )
    
    # Faz upload para S3
    photo_url = upload_image_to_s3(photo, folder="profile_photos")
    
    # Atualiza no banco
    return ProfileController.update_profile_photo(db, user, photo_url)

@router.get("/profile/{user_id}", response_model=ProfileResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    """Retorna os dados do perfil de um usuário específico"""
    return ProfileController.get_user_profile(db, user_id)






