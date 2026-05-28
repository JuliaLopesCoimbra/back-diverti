from app.domain.users.repositories.notification_preference_repository import NotificationPreferenceRepository

class NotificationPreferenceService:
    
    @staticmethod
    def get_preferences(notification_db, user_id: int):
        """Retorna preferências do usuário (cria se não existir)"""
        return NotificationPreferenceRepository.get_or_create(notification_db, user_id)
    
    @staticmethod
    def update_preferences(notification_db, user_id: int, preferences: dict):
        """Atualiza preferências do usuário"""
        return NotificationPreferenceRepository.update(
            notification_db,
            user_id,
            lineup_updated=preferences.get("lineup_updated"),
            news_feed=preferences.get("news_feed"),
            interactions=preferences.get("interactions"),
            new_events=preferences.get("new_events"),
            push_enabled=preferences.get("push_enabled"),
        )
    
    @staticmethod
    def is_enabled(notification_db, user_id: int, notification_type: str) -> bool:
        """
        Verifica se um tipo de notificação está habilitado para o usuário.
        
        notification_type: 'lineup_updated', 'news_feed', 'interactions', 'new_events'
        """
        preference = NotificationPreferenceRepository.get_or_create(notification_db, user_id)
        
        if notification_type == "lineup_updated":
            return preference.lineup_updated
        elif notification_type == "news_feed":
            return preference.news_feed
        elif notification_type == "interactions":
            return preference.interactions
        elif notification_type == "new_events":
            return preference.new_events
        
        return True  # Por padrão, permite se tipo desconhecido

