from sqlalchemy.orm import Session
from app.domain.auth.models.social_account_model import SocialAccount

class SocialRepository:

    @staticmethod
    def get_by_provider(db: Session, provider: str, provider_user_id: str):
        return db.query(SocialAccount).filter(
            SocialAccount.provider == provider,
            SocialAccount.provider_user_id == provider_user_id
        ).first()

    @staticmethod
    def create(db: Session, user_id: int, provider: str, provider_user_id: str,
               access_token=None, refresh_token=None, expires_at=None):
        social = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(social)
        db.commit()
        db.refresh(social)
        return social
