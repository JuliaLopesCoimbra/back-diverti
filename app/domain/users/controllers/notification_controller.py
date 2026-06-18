from fastapi import HTTPException
from app.domain.users.repositories.notification_repository import NotificationRepository
from app.domain.users.services.notification_service import NotificationService
from app.domain.users.schemas.notification_schema import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
    RelatedUserInfo,
    BroadcastNotificationRequest,
    BroadcastNotificationResponse
)
from app.domain.auth.models.user_model import User

class NotificationController:
    
    @staticmethod
    def list(notification_db, auth_db, user_id: int, limit: int = 20, offset: int = 0, unread_only: bool = False):
        """Lista notificações do usuário"""
        notifications = NotificationRepository.list_by_user(
            notification_db, user_id, limit, offset, unread_only
        )
        total = NotificationRepository.count_by_user(notification_db, user_id, False)
        unread_count = NotificationRepository.count_by_user(notification_db, user_id, True)
        
        # Busca dados dos usuários relacionados
        notification_responses = []
        for notification in notifications:
            notification_dict = NotificationResponse.model_validate(notification).model_dump()
            
            # Se tem related_user_id, busca os dados do usuário
            if notification.related_user_id:
                related_user = auth_db.query(User).filter(User.id == notification.related_user_id).first()
                if related_user:
                    notification_dict['related_user'] = RelatedUserInfo(
                        id=related_user.id,
                        name=related_user.name,
                        profile_photo=related_user.profile_photo
                    ).model_dump()
            
            # Se tem broadcast_sender_id, busca os dados do admin/admin_master que enviou
            if notification.broadcast_sender_id:
                broadcast_sender = auth_db.query(User).filter(User.id == notification.broadcast_sender_id).first()
                if broadcast_sender:
                    notification_dict['broadcast_sender'] = RelatedUserInfo(
                        id=broadcast_sender.id,
                        name=broadcast_sender.name,
                        profile_photo=broadcast_sender.profile_photo
                    ).model_dump()
            
            notification_responses.append(NotificationResponse(**notification_dict))
        
        return NotificationListResponse(
            notifications=notification_responses,
            total=total,
            unread_count=unread_count
        )
    
    @staticmethod
    def get_unread_count(notification_db, user_id: int):
        """Retorna contagem de notificações não lidas"""
        count = NotificationRepository.count_by_user(notification_db, user_id, True)
        return UnreadCountResponse(unread_count=count)
    
    @staticmethod
    def mark_as_read(notification_db, auth_db, notification_id: int, user_id: int):
        """Marca uma notificação como lida"""
        notification = NotificationRepository.mark_as_read(notification_db, notification_id, user_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        
        # Busca dados do usuário relacionado se houver
        notification_dict = NotificationResponse.model_validate(notification).model_dump()
        if notification.related_user_id:
            from app.domain.auth.models.user_model import User
            related_user = auth_db.query(User).filter(User.id == notification.related_user_id).first()
            if related_user:
                notification_dict['related_user'] = RelatedUserInfo(
                    id=related_user.id,
                    name=related_user.name,
                    profile_photo=related_user.profile_photo
                ).model_dump()
        
        # Se tem broadcast_sender_id, busca os dados do admin/admin_master que enviou
        if notification.broadcast_sender_id:
            from app.domain.auth.models.user_model import User
            broadcast_sender = auth_db.query(User).filter(User.id == notification.broadcast_sender_id).first()
            if broadcast_sender:
                notification_dict['broadcast_sender'] = RelatedUserInfo(
                    id=broadcast_sender.id,
                    name=broadcast_sender.name,
                    profile_photo=broadcast_sender.profile_photo
                ).model_dump()
        
        return NotificationResponse(**notification_dict)
    
    @staticmethod
    def mark_all_as_read(notification_db, user_id: int):
        """Marca todas as notificações do usuário como lidas"""
        count = NotificationRepository.mark_all_as_read(notification_db, user_id)
        return {"message": f"{count} notificações marcadas como lidas", "count": count}
    
    @staticmethod
    def broadcast(notification_db, auth_db, request: BroadcastNotificationRequest, sender_id: int):
        """Envia uma notificação para todos os usuários ativos do sistema via Celery"""
        try:
            from app.domain.users.tasks.notification_tasks import broadcast_notification_task
            broadcast_notification_task.delay(
                title=request.title,
                message=request.message,
                sender_id=sender_id
            )
            # Retorna imediatamente, a task processará em background
            return BroadcastNotificationResponse(
                message="Notificação enviada para processamento",
                users_notified=0  # Será processado em background
            )
        except Exception as e:
            # Se Celery não estiver disponível, tenta processar síncrono como fallback
            try:
                users_notified = NotificationService.broadcast_notification(
                    notification_db,
                    auth_db,
                    title=request.title,
                    message=request.message,
                    sender_id=sender_id
                )
                return BroadcastNotificationResponse(
                    message=f"Notificação enviada com sucesso para {users_notified} usuários",
                    users_notified=users_notified
                )
            except Exception as fallback_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao enviar notificação: {str(fallback_error)}"
                )

