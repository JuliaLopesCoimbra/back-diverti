# app/domain/users/repositories/profile_repository.py

from sqlalchemy.orm import Session
from app.domain.auth.models.user_model import User
from datetime import datetime, timezone
from typing import Optional

class ProfileRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_profile_photo(db: Session, user: User, photo_url: str):
        # Recarrega o usuário da sessão atual para garantir que está anexado
        user = db.query(User).filter(User.id == user.id).first()
        if not user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        user.profile_photo = photo_url
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_profile(
        db: Session, 
        user: User, 
        birth_date: Optional[datetime] = None,
        gender: Optional[str] = None
    ):
        """Atualiza os dados do perfil do usuário"""
        # Recarrega o usuário da sessão atual para garantir que está anexado
        user = db.query(User).filter(User.id == user.id).first()
        if not user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        if birth_date is not None:
            user.birth_date = birth_date
        if gender is not None:
            user.gender = gender
        
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user






