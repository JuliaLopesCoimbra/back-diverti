# app/domain/admin/controllers/event_controller.py
from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.services.event_service import EventService

class EventController:

    @staticmethod
    def create(db, data, user):
        return EventService.create_event(db, data, user)

    @staticmethod
    def list(db, limit: int = 50, offset: int = 0):
        return EventService.list(db, limit, offset)

    @staticmethod
    def update(db, event_id: int, data: dict, user):
        return EventService.update_event(db, event_id, data, user)

    @staticmethod
    def get(db, event_id: int, user=None):
        return EventService.get_event(db, event_id, user)

    @staticmethod
    def delete(db, event_id: int, user):
        return EventService.delete_event(db, event_id, user)

    @staticmethod
    def change_status(db, event_id: int, is_active: bool, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem alterar status")

        # force_db=True para garantir objeto SQLAlchemy
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        old_status = event.is_active
        event = EventRepository.set_status(db, event, is_active, user.id)
        
        # Gerencia notificações baseado na mudança de status via Celery
        try:
            if not is_active and old_status:
                # Evento foi desativado: remove notificações (síncrono, pois é rápido)
                from app.config.notification_db import get_notification_db
                from app.domain.users.services.notification_service import NotificationService
                notification_db = next(get_notification_db())
                try:
                    NotificationService.remove_event_notifications(notification_db, event_id)
                finally:
                    notification_db.close()
            elif is_active:
                # Evento foi ativado (primeira vez ou reativado): cria notificações via Celery
                from app.domain.users.tasks.notification_tasks import restore_event_notifications_task
                restore_event_notifications_task.delay(event_id)
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao gerenciar notificações de evento: {e}")
        
        return event
    
    @staticmethod
    def update_post_approval_requirement(db, event_id: int, requires_approval: bool, user):
        return EventService.update_post_approval_requirement(db, event_id, requires_approval, user)