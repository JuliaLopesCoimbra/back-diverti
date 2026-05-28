from sqlalchemy.orm import Session
from app.domain.users.models.notification_preference_model import NotificationPreference

class NotificationPreferenceRepository:
    
    @staticmethod
    def get_by_user(db: Session, user_id: int):
        """Busca preferências do usuário ou retorna None"""
        return db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
    
    @staticmethod
    def get_or_create(db: Session, user_id: int):
        """Busca preferências ou cria com valores padrão (todos True)"""
        preference = NotificationPreferenceRepository.get_by_user(db, user_id)
        
        if not preference:
            preference = NotificationPreference(
                user_id=user_id,
                lineup_updated=True,
                news_feed=True,
                interactions=True,
                new_events=True,
                push_enabled=False,
            )
            db.add(preference)
            db.commit()
            db.refresh(preference)
        
        return preference
    
    @staticmethod
    def update(db: Session, user_id: int, lineup_updated: bool = None,
               news_feed: bool = None, interactions: bool = None, new_events: bool = None,
               push_enabled: bool = None):
        """Atualiza preferências do usuário"""
        preference = NotificationPreferenceRepository.get_or_create(db, user_id)

        if lineup_updated is not None:
            preference.lineup_updated = lineup_updated
        if news_feed is not None:
            preference.news_feed = news_feed
        if interactions is not None:
            preference.interactions = interactions
        if new_events is not None:
            preference.new_events = new_events
        if push_enabled is not None:
            preference.push_enabled = push_enabled

        db.commit()
        db.refresh(preference)
        return preference

