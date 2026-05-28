# app/domain/admin/services/event_service.py

from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.photo_ai.services.rekognition_service import RekognitionService
from app.infra.redis import redis_client, CacheKeys

class EventService:

    @staticmethod
    def create_event(db, data, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem criar eventos")

        # Adiciona created_by_id ao data
        data["created_by_id"] = user.id
        
        event = EventRepository.create(db, data)

        EventService._setup_photo_ai_resources(event)
        
        # Invalida cache de eventos
        redis_client.delete(CacheKeys.events_list())
        
        # Notificar todos os usuários sobre o novo evento via Celery
        try:
            from app.domain.users.tasks.notification_tasks import notify_new_event_task
            notify_new_event_task.delay(event.id)
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao enviar notificação de novo evento para Celery: {e}")
        
        return event

    @staticmethod
    def list(db, limit: int = 50, offset: int = 0):
        return EventRepository.list(db, limit=limit, offset=offset)

    @staticmethod
    def update_event(db, event_id: int, data: dict, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem editar eventos")

        # force_db=True para garantir objeto SQLAlchemy
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        # Verificar se line_up foi atualizado
        lineup_updated = 'line_up' in data and event.line_up != data.get('line_up')
        
        # Adiciona updated_by_id ao data
        data["updated_by_id"] = user.id
        
        result = EventRepository.update(db, event, data)
        
        # Invalida cache relacionado
        redis_client.delete(CacheKeys.events_list())
        redis_client.delete(CacheKeys.event_details(event_id))
        redis_client.delete_pattern(f"news:event:{event_id}:*")
        
        # Criar notificação se line_up foi atualizado via Celery
        if lineup_updated:
            try:
                from app.domain.users.tasks.notification_tasks import notify_lineup_updated_task
                notify_lineup_updated_task.delay(event_id)
            except Exception as e:
                # Não quebra o fluxo se a notificação falhar
                print(f"Erro ao enviar notificação de line up para Celery: {e}")
        
        return result
    
    @staticmethod
    def _setup_photo_ai_resources(event) -> None:
        try:
            collection_id = str(event.id)
            service = RekognitionService()
            service.preparar_recursos_evento(collection_id)
        except Exception as e:
            # Log simples para diagnóstico sem quebrar o fluxo de criação
            print(f"Falha ao preparar recursos de IA para evento {getattr(event, 'id', '?')}: {e}")

    @staticmethod
    def get_event(db, event_id: int, user=None):
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Evento não encontrado")
        return event

    @staticmethod
    def delete_event(db, event_id: int, user):
        from datetime import datetime
        
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem deletar eventos")

        # force_db=True para garantir objeto SQLAlchemy
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        # Verifica se o evento já foi deletado
        if event.deleted_at is not None:
            raise ValueError("Evento já foi deletado")

        # Soft delete: marca como deletado sem remover do banco
        event.deleted_at = datetime.utcnow()
        event.deleted_by_id = user.id
        
        db.commit()
        db.refresh(event)
        
        # Invalida cache relacionado
        redis_client.delete(CacheKeys.events_list())
        redis_client.delete(CacheKeys.event_details(event_id))
        redis_client.delete_pattern(f"news:event:{event_id}:*")
        
        # Remove notificações de novo evento quando evento é deletado
        try:
            from app.config.notification_db import get_notification_db
            from app.domain.users.services.notification_service import NotificationService
            notification_db = next(get_notification_db())
            try:
                NotificationService.remove_event_notifications(notification_db, event_id)
            finally:
                notification_db.close()
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao remover notificações de evento deletado: {e}")
        
        return event
    
    @staticmethod
    def update_post_approval_requirement(db, event_id: int, requires_approval: bool, user):
        """Atualiza se o evento requer aprovação de posts"""
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem alterar essa configuração")
        
        # force_db=True para garantir objeto SQLAlchemy
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")
        
        # Se está desativando a aprovação e há posts pendentes, aprova todos automaticamente
        if not requires_approval and event.requires_post_approval:
            from app.domain.admin.repositories.news_repository import NewsRepository
            pending_count = NewsRepository.count_pending_by_event(db, event_id)
            
            if pending_count > 0:
                # Aprova todos os posts pendentes automaticamente
                NewsRepository.approve_all_pending_by_event(db, event_id, user.id)
                return {
                    "event": EventRepository.update(db, event, {"requires_post_approval": requires_approval, "updated_by_id": user.id}),
                    "pending_posts_approved": pending_count
                }
        
        return {
            "event": EventRepository.update(db, event, {"requires_post_approval": requires_approval, "updated_by_id": user.id}),
            "pending_posts_approved": 0
        }