from sqlalchemy.orm import Session
from app.domain.users.models.push_subscription_model import PushSubscription


class PushSubscriptionRepository:
    @staticmethod
    def create(
        db: Session,
        user_id: int,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str = None,
    ):
        """Cria ou atualiza assinatura (upsert por endpoint)."""
        existing = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint
        ).first()
        if existing:
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            if user_agent is not None:
                existing.user_agent = user_agent
            db.commit()
            db.refresh(existing)
            return existing
        sub = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            user_agent=user_agent,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def delete_by_endpoint(db: Session, endpoint: str, user_id: int):
        """Remove assinatura por endpoint (só do próprio usuário)."""
        deleted = db.query(PushSubscription).filter(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == user_id,
        ).delete()
        db.commit()
        return deleted > 0

    @staticmethod
    def get_by_user_id(db: Session, user_id: int):
        """Lista todas as assinaturas do usuário."""
        return db.query(PushSubscription).filter(
            PushSubscription.user_id == user_id
        ).all()
