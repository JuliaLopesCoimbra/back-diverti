from app.domain.users.services.notification_preference_service import NotificationPreferenceService
from app.domain.users.schemas.notification_preference_schema import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate
)

class NotificationPreferenceController:
    
    @staticmethod
    def get(notification_db, user_id: int):
        preference = NotificationPreferenceService.get_preferences(notification_db, user_id)
        return NotificationPreferenceResponse(
            user_id=preference.user_id,
            lineup_updated=preference.lineup_updated,
            news_feed=preference.news_feed,
            interactions=preference.interactions,
            new_events=preference.new_events,
            push_enabled=getattr(preference, "push_enabled", False),
        )

    @staticmethod
    def update(notification_db, user_id: int, data: NotificationPreferenceUpdate):
        preference = NotificationPreferenceService.update_preferences(
            notification_db,
            user_id,
            {
                "lineup_updated": data.lineup_updated,
                "news_feed": data.news_feed,
                "interactions": data.interactions,
                "new_events": data.new_events,
                "push_enabled": data.push_enabled,
            }
        )
        return NotificationPreferenceResponse(
            user_id=preference.user_id,
            lineup_updated=preference.lineup_updated,
            news_feed=preference.news_feed,
            interactions=preference.interactions,
            new_events=preference.new_events,
            push_enabled=getattr(preference, "push_enabled", False),
        )

