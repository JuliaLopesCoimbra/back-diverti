from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.domain.users.models.notification_model import Notification

class NotificationRepository:
    
    @staticmethod
    def create(db: Session, user_id: int, notification_type: str, title: str, message: str,
               related_user_id: int = None, related_news_id: int = None,
               related_comment_id: int = None, related_event_id: int = None, count: int = 1,
               broadcast_sender_id: int = None):
        """Cria uma nova notificação"""
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            related_user_id=related_user_id,
            related_news_id=related_news_id,
            related_comment_id=related_comment_id,
            related_event_id=related_event_id,
            count=count,
            broadcast_sender_id=broadcast_sender_id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def find_groupable_notification(db: Session, user_id: int, notification_type: str, 
                                     related_comment_id: int, is_read: bool = False):
        """Busca uma notificação não lida do mesmo tipo para o mesmo comentário que pode ser agrupada"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == notification_type,
            Notification.related_comment_id == related_comment_id,
            Notification.is_read == is_read
        ).order_by(desc(Notification.created_at)).first()
    
    @staticmethod
    def find_groupable_reply_notification(db: Session, user_id: int, parent_comment_id: int, 
                                          interaction_db, is_read: bool = False):
        """Busca uma notificação não lida de comment_reply para o mesmo comentário pai"""
        from app.domain.users.models.comment_model import Comment
        
        # Busca todas as notificações de comment_reply não lidas para este usuário
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == "comment_reply",
            Notification.is_read == is_read
        ).order_by(desc(Notification.created_at)).all()
        
        # Para cada notificação, verifica se o related_comment_id (resposta) tem o mesmo parent_comment_id
        for notification in notifications:
            if notification.related_comment_id:
                reply_comment = interaction_db.query(Comment).filter(
                    Comment.id == notification.related_comment_id
                ).first()
                if reply_comment and reply_comment.parent_comment_id == parent_comment_id:
                    return notification
        
        return None
    
    @staticmethod
    def increment_count(db: Session, notification_id: int, new_related_user_id: int, new_message: str):
        """Incrementa o contador de uma notificação agrupada e atualiza o último usuário e mensagem"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.count += 1
            notification.related_user_id = new_related_user_id
            notification.message = new_message
            # Atualiza created_at para a mais recente
            from datetime import datetime, timezone
            notification.created_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(notification)
        return notification
    
    @staticmethod
    def decrement_count(db: Session, notification_id: int, auth_db=None, liker_id: int = None):
        """Decrementa o contador de uma notificação agrupada e atualiza a mensagem se necessário"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            if notification.count > 1:
                old_count = notification.count
                notification.count -= 1
                
                # Se count voltar para 1, verifica se deve deletar ou atualizar
                if notification.count == 1:
                    # Se a pessoa que descurtiu é a última (related_user_id), deleta a notificação
                    if liker_id and notification.related_user_id == liker_id:
                        db.delete(notification)
                        db.commit()
                        return None
                    # Caso contrário, atualiza a mensagem para formato individual
                    elif auth_db:
                        from app.domain.auth.models.user_model import User
                        user = auth_db.query(User).filter(User.id == notification.related_user_id).first()
                        if user:
                            if notification.type == "comment_like":
                                notification.message = f"{user.name} curtiu seu comentário"
                                notification.title = "Alguém curtiu seu comentário"
                            elif notification.type == "comment_reply":
                                notification.message = f"{user.name} respondeu seu comentário"
                                notification.title = "Nova resposta ao seu comentário"
                            elif notification.type == "post_like":
                                notification.message = f"{user.name} curtiu seu post"
                                notification.title = "Alguém curtiu seu post"
                elif notification.count > 1:
                    # Atualiza mensagem para refletir o novo count (sempre atualiza quando count > 1)
                    if notification.type == "comment_like":
                        notification.message = f"{notification.count} pessoas curtiram seu comentário"
                        notification.title = "Pessoas curtiram seu comentário"
                    elif notification.type == "comment_reply":
                        notification.message = f"{notification.count} pessoas comentaram seu comentário"
                        notification.title = "Pessoas comentaram seu comentário"
                    elif notification.type == "post_like":
                        notification.message = f"{notification.count} pessoas curtiram seu post"
                        notification.title = "Pessoas curtiram seu post"
                
                # Sempre commita as mudanças (flush antes para garantir que as mudanças sejam persistidas)
                db.flush()
                db.commit()
                db.refresh(notification)
            else:
                # Se count já for 1, deleta a notificação
                db.delete(notification)
                db.commit()
                return None
        return notification
    
    @staticmethod
    def list_by_user(db: Session, user_id: int, limit: int = 20, offset: int = 0, unread_only: bool = False):
        """Lista notificações do usuário com paginação"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(desc(Notification.created_at)).limit(limit).offset(offset).all()
    
    @staticmethod
    def count_by_user(db: Session, user_id: int, unread_only: bool = False) -> int:
        """Conta notificações do usuário"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.count()
    
    @staticmethod
    def get_by_id(db: Session, notification_id: int):
        """Busca uma notificação por ID"""
        return db.query(Notification).filter(Notification.id == notification_id).first()
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int):
        """Marca uma notificação como lida"""
        from datetime import datetime, timezone
        
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(notification)
        
        return notification
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int):
        """Marca todas as notificações do usuário como lidas"""
        from datetime import datetime, timezone
        
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            'is_read': True,
            'read_at': datetime.now(timezone.utc)
        }, synchronize_session=False)
        
        db.commit()
        return count
    
    @staticmethod
    def delete_by_comment_like(db: Session, comment_id: int, liker_id: int, comment_owner_id: int, auth_db=None):
        """Remove notificação de like quando a curtida é removida (decrementa count se agrupada)"""
        # Busca notificação não lida do mesmo tipo e comentário
        notification = db.query(Notification).filter(
            Notification.user_id == comment_owner_id,
            Notification.type == "comment_like",
            Notification.related_comment_id == comment_id,
            Notification.is_read == False
        ).order_by(desc(Notification.created_at)).first()
        
        if notification:
            # Se a notificação está agrupada (count > 1), decrementa e verifica se deve deletar
            if notification.count > 1:
                result = NotificationRepository.decrement_count(db, notification.id, auth_db, liker_id)
                # Se decrement_count retornou None, a notificação foi deletada
                return result is None
            # Se count == 1 e o related_user_id corresponde, deleta
            elif notification.related_user_id == liker_id:
                db.delete(notification)
                db.commit()
                return True
        return False
    
    @staticmethod
    def find_groupable_post_like_notification(db: Session, user_id: int, news_id: int, is_read: bool = False):
        """Busca uma notificação não lida do tipo post_like para o mesmo post que pode ser agrupada"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == "post_like",
            Notification.related_news_id == news_id,
            Notification.is_read == is_read
        ).order_by(desc(Notification.created_at)).first()
    
    @staticmethod
    def delete_by_post_like(db: Session, news_id: int, liker_id: int, post_owner_id: int, auth_db=None):
        """Remove notificação de like quando a curtida do post é removida (decrementa count se agrupada)"""
        # Busca notificação não lida do mesmo tipo e post
        notification = db.query(Notification).filter(
            Notification.user_id == post_owner_id,
            Notification.type == "post_like",
            Notification.related_news_id == news_id,
            Notification.is_read == False
        ).order_by(desc(Notification.created_at)).first()
        
        if notification:
            # Se a notificação está agrupada (count > 1), decrementa e verifica se deve deletar
            if notification.count > 1:
                result = NotificationRepository.decrement_count(db, notification.id, auth_db, liker_id)
                # Se decrement_count retornou None, a notificação foi deletada
                return result is None
            # Se count == 1 e o related_user_id corresponde, deleta
            elif notification.related_user_id == liker_id:
                db.delete(notification)
                db.commit()
                return True
        return False
    
    @staticmethod
    def delete_by_comment_reply(db: Session, reply_id: int, reply_author_id: int, parent_comment_id: int,
                                 parent_comment_owner_id: int, interaction_db, auth_db=None):
        """Remove notificação de reply quando uma resposta é deletada (decrementa count se agrupada)"""
        # Busca notificação não lida do tipo comment_reply para o mesmo comentário pai
        notification = NotificationRepository.find_groupable_reply_notification(
            db,
            user_id=parent_comment_owner_id,
            parent_comment_id=parent_comment_id,
            interaction_db=interaction_db,
            is_read=False
        )
        
        # Se não encontrou, tenta buscar diretamente pela resposta (notificação individual)
        if not notification:
            notification = db.query(Notification).filter(
                Notification.user_id == parent_comment_owner_id,
                Notification.type == "comment_reply",
                Notification.related_comment_id == reply_id,
                Notification.is_read == False
            ).order_by(desc(Notification.created_at)).first()
        
        if notification:
            # Se a notificação está agrupada (count > 1), decrementa e verifica se deve deletar
            if notification.count > 1:
                result = NotificationRepository.decrement_count(db, notification.id, auth_db, reply_author_id)
                # Se decrement_count retornou None, a notificação foi deletada
                return result is None
            # Se count == 1 e o related_user_id corresponde, deleta
            elif notification.related_user_id == reply_author_id:
                db.delete(notification)
                db.commit()
                return True
        return False
    
    @staticmethod
    def delete_by_comment_id(db: Session, comment_id: int, interaction_db=None, auth_db=None,
                              comment_user_id: int = None, parent_comment_id: int = None):
        """Deleta todas as notificações relacionadas a um comentário (quando o comentário é deletado)"""
        from app.domain.users.repositories.comment_repository import CommentRepository
        
        # Se for uma resposta (tem parent_comment_id), tenta decrementar notificação agrupada
        reply_processed = False
        if parent_comment_id and comment_user_id and interaction_db:
            parent_comment = CommentRepository.get_by_id(interaction_db, parent_comment_id)
            if parent_comment:
                # Tenta remover/decrementar notificação agrupada de resposta
                reply_processed = NotificationRepository.delete_by_comment_reply(
                    db, comment_id, comment_user_id, parent_comment_id,
                    parent_comment.user_id, interaction_db, auth_db
                )
        
        # Deleta notificações de like e post_comment relacionadas a este comentário
        # Se reply foi processada (agrupada), não deleta notificações de reply aqui
        # (elas já foram tratadas no delete_by_comment_reply)
        # Se não foi processada, deleta notificações individuais de reply
        if reply_processed:
            # Apenas deleta notificações de like e post_comment
            count = db.query(Notification).filter(
                Notification.related_comment_id == comment_id,
                Notification.type.in_(["comment_like", "post_comment"])
            ).delete(synchronize_session=False)
        else:
            # Deleta todas as notificações relacionadas (incluindo reply individual)
            count = db.query(Notification).filter(
                Notification.related_comment_id == comment_id,
                Notification.type.in_(["comment_like", "post_comment", "comment_reply"])
            ).delete(synchronize_session=False)
        
        db.commit()
        return count
    
    @staticmethod
    def delete_by_news_id(db: Session, news_id: int):
        """Deleta todas as notificações relacionadas a um post (quando o post é deletado)"""
        # Deleta notificações de new_post e post_approved relacionadas a este post
        count = db.query(Notification).filter(
            Notification.related_news_id == news_id
        ).delete(synchronize_session=False)
        
        db.commit()
        return count
    
    @staticmethod
    def delete_by_event_id(db: Session, event_id: int, notification_type: str = None):
        """Deleta todas as notificações relacionadas a um evento"""
        query = db.query(Notification).filter(
            Notification.related_event_id == event_id
        )
        
        # Se especificado, filtra por tipo de notificação
        if notification_type:
            query = query.filter(Notification.type == notification_type)
        
        count = query.delete(synchronize_session=False)
        db.commit()
        return count

