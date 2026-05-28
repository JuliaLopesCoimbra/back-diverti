# app/domain/users/services/profile_service.py

from sqlalchemy.orm import Session
from app.domain.users.repositories.profile_repository import ProfileRepository
from app.domain.auth.models.user_model import User
from app.infra.redis import redis_client, CacheKeys
from datetime import datetime
from typing import Optional

class ProfileService:

    @staticmethod
    def get_profile(db: Session, user: User):
        """Retorna os dados do perfil do usuário"""
        # Nota: Não usamos cache aqui porque o FastAPI precisa do objeto SQLAlchemy
        # e objetos SQLAlchemy não são facilmente serializáveis para JSON
        # O cache seria mais útil em endpoints que retornam dados já serializados
        return ProfileRepository.get_by_id(db, user.id)

    @staticmethod
    def update_profile_photo(db: Session, user: User, photo_url: str):
        """Atualiza a foto de perfil do usuário e invalida cache"""
        result = ProfileRepository.update_profile_photo(db, user, photo_url)
        # Invalida cache do perfil e do /me
        redis_client.delete(CacheKeys.user_profile(user.id))
        redis_client.delete(CacheKeys.user_me(user.id))
        return result

    @staticmethod
    def update_profile(
        db: Session, 
        user: User, 
        birth_date: Optional[datetime] = None,
        gender: Optional[str] = None
    ):
        """Atualiza os dados do perfil do usuário e invalida cache"""
        result = ProfileRepository.update_profile(db, user, birth_date, gender)
        # Invalida cache do perfil e do /me
        redis_client.delete(CacheKeys.user_profile(user.id))
        redis_client.delete(CacheKeys.user_me(user.id))
        return result

    @staticmethod
    def get_user_profile(db: Session, user_id: int):
        """Retorna os dados do perfil de um usuário específico"""
        user = ProfileRepository.get_by_id(db, user_id)
        if not user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        return user

