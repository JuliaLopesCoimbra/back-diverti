from sqlalchemy.orm import Session
from app.domain.auth.models.password_reset_model import PasswordResetToken
from datetime import datetime

class PasswordResetRepository:

    @staticmethod
    def create_token(db: Session, user_id: int, token: str, expires_at):
        model = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(model)
        db.commit()
        return model

    @staticmethod
    def get_token(db: Session, token: str):
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used_at == None
        ).first()

    @staticmethod
    def mark_used(db: Session, model: PasswordResetToken):
        model.used_at = datetime.utcnow()
        db.commit()
