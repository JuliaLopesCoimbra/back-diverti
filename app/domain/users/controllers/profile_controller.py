# app/domain/users/controllers/profile_controller.py

from app.domain.users.services.profile_service import ProfileService
from datetime import datetime, timezone, date
from typing import Optional

class ProfileController:

    @staticmethod
    def get_profile(db, user):
        return ProfileService.get_profile(db, user)

    @staticmethod
    def update_profile_photo(db, user, photo_url):
        return ProfileService.update_profile_photo(db, user, photo_url)

    @staticmethod
    def update_profile(db, user, birth_date: Optional[date] = None, gender: Optional[str] = None):
        """Atualiza os dados do perfil do usuário"""
        # Converte date para datetime com timezone UTC
        birth_date_dt = None
        if birth_date:
            birth_date_dt = datetime.combine(birth_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        
        return ProfileService.update_profile(db, user, birth_date_dt, gender)

    @staticmethod
    def get_user_profile(db, user_id: int):
        return ProfileService.get_user_profile(db, user_id)






