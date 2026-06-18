from app.domain.users.repositories.notification_repository import NotificationRepository
from app.domain.users.repositories.notification_preference_repository import NotificationPreferenceRepository
from app.domain.auth.models.user_model import User


def _enqueue_browser_push(notification_id: int) -> None:
    """Enfileira envio de Web Push ao navegador (import tardio para evitar dependência circular)."""
    from app.domain.users.tasks.push_tasks import send_push_for_notification_task
    send_push_for_notification_task.delay(notification_id)


class NotificationService:
    
    @staticmethod
    def create_notification(
        notification_db,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        related_user_id: int = None,
        related_news_id: int = None,
        related_comment_id: int = None,
        related_event_id: int = None,
        count: int = 1,
        broadcast_sender_id: int = None
    ):
        """Cria uma nova notificação"""
        notification = NotificationRepository.create(
            notification_db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_user_id=related_user_id,
            related_news_id=related_news_id,
            related_comment_id=related_comment_id,
            related_event_id=related_event_id,
            count=count,
            broadcast_sender_id=broadcast_sender_id
        )
        # Enfileira envio de notificação ao navegador (Web Push, como app no dispositivo)
        _enqueue_browser_push(notification.id)
        return notification
    
    @staticmethod
    def notify_comment_reply(notification_db, auth_db, interaction_db, parent_comment_id: int, reply_author_id: int, reply_id: int):
        """Notifica quando alguém responde um comentário (agrupa com notificações não lidas do mesmo comentário)"""
        from app.domain.users.repositories.comment_repository import CommentRepository
        
        parent_comment = CommentRepository.get_by_id(interaction_db, parent_comment_id)
        if not parent_comment or parent_comment.user_id == reply_author_id:
            return  # Não notificar a si mesmo
        
        # VERIFICAR PREFERÊNCIA
        if not NotificationPreferenceRepository.get_or_create(notification_db, parent_comment.user_id).interactions:
            return  # Usuário desabilitou notificações de interações
        
        # Busca dados do autor da resposta
        reply_author = auth_db.query(User).filter(User.id == reply_author_id).first()
        if not reply_author:
            return
        
        # Busca notificação não lida do mesmo tipo para o mesmo comentário pai
        # Usa parent_comment_id para agrupar todas as respostas ao mesmo comentário
        existing_notification = NotificationRepository.find_groupable_reply_notification(
            notification_db,
            user_id=parent_comment.user_id,
            parent_comment_id=parent_comment_id,
            interaction_db=interaction_db,
            is_read=False
        )
        
        if existing_notification:
            # Atualiza notificação existente incrementando o count
            if existing_notification.count == 1:
                # Primeira vez agrupando: muda de "FULANO comentou" para "2 pessoas comentaram"
                new_message = f"2 pessoas comentaram seu comentário"
                new_title = "Pessoas comentaram seu comentário"
            else:
                # Já estava agrupada: incrementa o número
                new_message = f"{existing_notification.count + 1} pessoas comentaram seu comentário"
                new_title = "Pessoas comentaram seu comentário"
            
            NotificationRepository.increment_count(
                notification_db,
                existing_notification.id,
                new_related_user_id=reply_author_id,
                new_message=new_message
            )
            # Atualiza o título também
            existing_notification.title = new_title
            # Atualiza related_comment_id para apontar para a última resposta (para scroll)
            existing_notification.related_comment_id = reply_id
            notification_db.commit()
            _enqueue_browser_push(existing_notification.id)
        else:
            # Primeiro comentário: cria notificação individual
            # related_comment_id armazena o ID da resposta (reply) para fazer scroll direto até ela
            NotificationService.create_notification(
                notification_db,
                user_id=parent_comment.user_id,
                notification_type="comment_reply",
                title="Nova resposta ao seu comentário",
                message=f"{reply_author.name} respondeu seu comentário",
                related_user_id=reply_author_id,
                related_news_id=parent_comment.news_id,
                related_comment_id=reply_id,  # ID da resposta, não do comentário pai
                count=1
            )
    
    @staticmethod
    def notify_comment_like(notification_db, auth_db, interaction_db, comment_id: int, liker_id: int):
        """Notifica quando alguém curte um comentário (agrupa com notificações não lidas do mesmo comentário)"""
        from app.domain.users.repositories.comment_repository import CommentRepository
        
        comment = CommentRepository.get_by_id(interaction_db, comment_id)
        if not comment or comment.user_id == liker_id:
            return  # Não notificar a si mesmo
        
        # VERIFICAR PREFERÊNCIA
        if not NotificationPreferenceRepository.get_or_create(notification_db, comment.user_id).interactions:
            return  # Usuário desabilitou notificações de interações
        
        liker = auth_db.query(User).filter(User.id == liker_id).first()
        if not liker:
            return
        
        # Busca notificação não lida do mesmo tipo para o mesmo comentário
        existing_notification = NotificationRepository.find_groupable_notification(
            notification_db,
            user_id=comment.user_id,
            notification_type="comment_like",
            related_comment_id=comment_id,
            is_read=False
        )
        
        if existing_notification:
            # Atualiza notificação existente incrementando o count
            if existing_notification.count == 1:
                # Primeira vez agrupando: muda de "FULANO curtiu" para "2 pessoas curtiram"
                new_message = f"2 pessoas curtiram seu comentário"
                new_title = "Pessoas curtiram seu comentário"
            else:
                # Já estava agrupada: incrementa o número
                new_message = f"{existing_notification.count + 1} pessoas curtiram seu comentário"
                new_title = "Pessoas curtiram seu comentário"
            
            NotificationRepository.increment_count(
                notification_db,
                existing_notification.id,
                new_related_user_id=liker_id,
                new_message=new_message
            )
            # Atualiza o título também
            existing_notification.title = new_title
            notification_db.commit()
            _enqueue_browser_push(existing_notification.id)
        else:
            # Primeira curtida: cria notificação individual
            NotificationService.create_notification(
                notification_db,
                user_id=comment.user_id,
                notification_type="comment_like",
                title="Alguém curtiu seu comentário",
                message=f"{liker.name} curtiu seu comentário",
                related_user_id=liker_id,
                related_news_id=comment.news_id,
                related_comment_id=comment_id,
                count=1
            )
    
    @staticmethod
    def notify_post_approved(notification_db, auth_db, admin_db, news_id: int, approver_id: int):
        """Notifica quando um post é aprovado (apenas para usuários comuns, não admin/patrocinador)"""
        from app.domain.admin.models.news_model import NewsPost
        from app.domain.admin.models.event_model import Event
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post or post.author_id == approver_id:
            return
        
        # Buscar o autor do post
        author = auth_db.query(User).filter(User.id == post.author_id).first()
        if not author:
            return
        
        # Não envia notificação para admin/patrocinador (eles recebem notify_post_approved_admin)
        if author.role in ["admin", "patrocinador"]:
            return
        
        approver = auth_db.query(User).filter(User.id == approver_id).first()
        if not approver:
            return
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == post.event_id).first()
        event_name = event.title if event else "evento"
        
        # Verificar preferência (assumindo que aprovação de post é tipo "news_feed")
        preference = NotificationPreferenceRepository.get_or_create(notification_db, post.author_id)
        if not preference.news_feed:
            return
        
        NotificationService.create_notification(
            notification_db,
            user_id=post.author_id,
            notification_type="post_approved",
            title="Seu post foi aprovado!",
            message=f"Seu post do evento {event_name} foi aprovado",
            related_user_id=approver_id,
            related_news_id=news_id,
            related_event_id=post.event_id
        )
    
    @staticmethod
    def notify_new_post(notification_db, auth_db, admin_db, news_id: int, event_id: int):
        """Notifica todos os usuários sobre novo post (opcional - pode ser muito pesado)"""
        from app.domain.admin.models.event_model import Event
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == event_id).first()
        event_name = event.title if event else "evento"
        
        # Buscar todos os usuários ativos
        all_users = auth_db.query(User).filter(User.status == "active").all()
        
        for user in all_users:
            # VERIFICAR PREFERÊNCIA
            preference = NotificationPreferenceRepository.get_or_create(notification_db, user.id)
            if preference.news_feed:
                NotificationService.create_notification(
                    notification_db,
                    user_id=user.id,
                    notification_type="new_post",
                    title="Novo post publicado!",
                    message=f"Post publicado no evento {event_name}",
                    related_news_id=news_id,
                    related_event_id=event_id
                )
    
    @staticmethod
    def notify_lineup_updated(notification_db, auth_db, admin_db, event_id: int):
        """Notifica quando o line up de um evento é atualizado"""
        from app.domain.admin.models.event_model import Event
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == event_id).first()
        event_name = event.title if event else "evento"
        
        # Buscar todos os usuários ativos
        all_users = auth_db.query(User).filter(User.status == "active").all()
        
        for user in all_users:
            # VERIFICAR PREFERÊNCIA
            preference = NotificationPreferenceRepository.get_or_create(notification_db, user.id)
            if preference.lineup_updated:
                NotificationService.create_notification(
                    notification_db,
                    user_id=user.id,
                    notification_type="lineup_updated",
                    title="Line up atualizado!",
                    message=f"Line up do evento {event_name} atualizado",
                    related_event_id=event_id
                )
    
    @staticmethod
    def notify_post_like(notification_db, auth_db, admin_db, news_id: int, liker_id: int):
        """Notifica quando alguém curte um post (agrupa com notificações não lidas do mesmo post)"""
        import logging
        logger = logging.getLogger(__name__)
        
        from app.domain.admin.models.news_model import NewsPost
        
        # logger.info(f"🔍 notify_post_like chamado: news_id={news_id}, liker_id={liker_id}")
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post:
            # logger.warning(f"⚠️ Post não encontrado: news_id={news_id}")
            return
        if not post.author_id:
            # logger.warning(f"⚠️ Post sem author_id: news_id={news_id}")
            return
        if post.author_id == liker_id:
            # logger.info(f"ℹ️ Autor curtindo próprio post - não notifica: news_id={news_id}, author_id={post.author_id}, liker_id={liker_id}")
            return  # Não notificar se o autor está curtindo o próprio post
        
        # logger.info(f"✅ Post encontrado: news_id={news_id}, author_id={post.author_id}")
        
        # VERIFICAR PREFERÊNCIA
        preference = NotificationPreferenceRepository.get_or_create(notification_db, post.author_id)
        # logger.info(f"🔍 Preferência do usuário {post.author_id}: interactions={preference.interactions}")
        if not preference.interactions:
            # logger.info(f"ℹ️ Usuário {post.author_id} desabilitou notificações de interações")
            return  # Usuário desabilitou notificações de interações
        
        liker = auth_db.query(User).filter(User.id == liker_id).first()
        if not liker:
            # logger.warning(f"⚠️ Usuário que curtiu não encontrado: liker_id={liker_id}")
            return
        
        # logger.info(f"✅ Criando notificação de curtida: user_id={post.author_id}, liker={liker.name}")
        
        # Busca notificação não lida do mesmo tipo para o mesmo post
        existing_notification = NotificationRepository.find_groupable_post_like_notification(
            notification_db,
            user_id=post.author_id,
            news_id=news_id,
            is_read=False
        )
        
        if existing_notification:
            # logger.info(f"📦 Notificação existente encontrada, agrupando: notification_id={existing_notification.id}, count={existing_notification.count}")
            # Atualiza notificação existente incrementando o count
            if existing_notification.count == 1:
                # Primeira vez agrupando: muda de "FULANO curtiu" para "2 pessoas curtiram"
                new_message = f"2 pessoas curtiram seu post"
                new_title = "Pessoas curtiram seu post"
            else:
                # Já estava agrupada: incrementa o número
                new_message = f"{existing_notification.count + 1} pessoas curtiram seu post"
                new_title = "Pessoas curtiram seu post"
            
            NotificationRepository.increment_count(
                notification_db,
                existing_notification.id,
                new_related_user_id=liker_id,
                new_message=new_message
            )
            # Atualiza o título também
            existing_notification.title = new_title
            notification_db.commit()
            _enqueue_browser_push(existing_notification.id)
            # logger.info(f"✅ Notificação atualizada: notification_id={existing_notification.id}, novo_count={existing_notification.count + 1}")
        else:
            # logger.info(f"📝 Criando nova notificação de curtida...")
            # Primeira curtida: cria notificação individual
            notification = NotificationService.create_notification(
                notification_db,
                user_id=post.author_id,
                notification_type="post_like",
                title="Alguém curtiu seu post",
                message=f"{liker.name} curtiu seu post",
                related_user_id=liker_id,
                related_news_id=news_id,
                count=1
            )
            # logger.info(f"✅ Nova notificação criada: notification_id={notification.id if notification else 'None'}")
    
    @staticmethod
    def remove_comment_like_notification(notification_db, interaction_db, comment_id: int, liker_id: int, auth_db=None):
        """Remove notificação quando alguém descurte um comentário"""
        from app.domain.users.repositories.comment_repository import CommentRepository
        
        comment = CommentRepository.get_by_id(interaction_db, comment_id)
        if not comment:
            return
        
        NotificationRepository.delete_by_comment_like(
            notification_db,
            comment_id,
            liker_id,
            comment.user_id,
            auth_db
        )
    
    @staticmethod
    def remove_post_like_notification(notification_db, admin_db, news_id: int, liker_id: int, auth_db=None):
        """Remove notificação quando alguém descurte um post"""
        from app.domain.admin.models.news_model import NewsPost
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post or not post.author_id:
            return
        
        NotificationRepository.delete_by_post_like(
            notification_db,
            news_id,
            liker_id,
            post.author_id,
            auth_db
        )
    
    @staticmethod
    def notify_post_comment(notification_db, auth_db, admin_db, news_id: int, comment_id: int, comment_author_id: int):
        """Notifica o autor do post quando alguém comenta diretamente no post"""
        import logging
        logger = logging.getLogger(__name__)
        
        from app.domain.admin.models.news_model import NewsPost
        
        # logger.info(f"🔍 notify_post_comment chamado: news_id={news_id}, comment_id={comment_id}, comment_author_id={comment_author_id}")
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post:
            # logger.warning(f"⚠️ Post não encontrado: news_id={news_id}")
            return
        if not post.author_id:
            # logger.warning(f"⚠️ Post sem author_id: news_id={news_id}")
            return
        if post.author_id == comment_author_id:
            # logger.info(f"ℹ️ Autor comentando no próprio post - não notifica: news_id={news_id}, author_id={post.author_id}, comment_author_id={comment_author_id}")
            return  # Não notificar se o autor está comentando no próprio post
        
        # logger.info(f"✅ Post encontrado: news_id={news_id}, author_id={post.author_id}")
        
        # VERIFICAR PREFERÊNCIA
        preference = NotificationPreferenceRepository.get_or_create(notification_db, post.author_id)
        # logger.info(f"🔍 Preferência do usuário {post.author_id}: interactions={preference.interactions}")
        if not preference.interactions:
            # logger.info(f"ℹ️ Usuário {post.author_id} desabilitou notificações de interações")
            return  # Usuário desabilitou notificações de interações
        
        # Busca dados do autor do comentário
        comment_author = auth_db.query(User).filter(User.id == comment_author_id).first()
        if not comment_author:
            # logger.warning(f"⚠️ Autor do comentário não encontrado: comment_author_id={comment_author_id}")
            return
        
        # logger.info(f"✅ Criando notificação: user_id={post.author_id}, comment_author={comment_author.name}")
        
        # related_comment_id armazena o ID do comentário para fazer scroll direto até ele
        notification = NotificationService.create_notification(
            notification_db,
            user_id=post.author_id,
            notification_type="post_comment",
            title="Novo comentário no seu post",
            message=f"{comment_author.name} comentou no seu post",
            related_user_id=comment_author_id,
            related_news_id=news_id,
            related_comment_id=comment_id
        )
        
        # logger.info(f"✅ Notificação criada com sucesso: notification_id={notification.id if notification else 'None'}")
    
    @staticmethod
    def remove_comment_notifications(notification_db, comment_id: int, interaction_db=None, auth_db=None, 
                                     comment_user_id: int = None, parent_comment_id: int = None):
        """Remove todas as notificações relacionadas a um comentário quando ele é deletado"""
        NotificationRepository.delete_by_comment_id(
            notification_db, comment_id, interaction_db, auth_db, comment_user_id, parent_comment_id
        )
    
    @staticmethod
    def remove_post_notifications(notification_db, news_id: int):
        """Remove todas as notificações relacionadas a um post quando ele é deletado"""
        NotificationRepository.delete_by_news_id(notification_db, news_id)
    
    @staticmethod
    def notify_post_approved_admin(notification_db, auth_db, admin_db, news_id: int, approver_id: int):
        """Notifica admin/patrocinador quando seu post é aprovado (sempre envia, sem verificar preferências)"""
        from app.domain.admin.models.news_model import NewsPost
        from app.domain.admin.models.event_model import Event
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post or not post.author_id:
            return
        
        # Buscar o autor do post
        author = auth_db.query(User).filter(User.id == post.author_id).first()
        if not author:
            return
        
        # Só notifica se o autor for admin ou patrocinador
        if author.role not in ["admin", "patrocinador"]:
            return
        
        # Não notifica a si mesmo se o aprovador for o próprio autor
        if post.author_id == approver_id:
            return
        
        approver = auth_db.query(User).filter(User.id == approver_id).first()
        if not approver:
            return
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == post.event_id).first()
        event_name = event.title if event else "evento"
        
        # Sempre cria notificação (sem verificar preferências)
        NotificationService.create_notification(
            notification_db,
            user_id=post.author_id,
            notification_type="post_approved_admin",
            title="Seu post foi aprovado!",
            message=f"Seu post do evento {event_name} foi aprovado por {approver.name}",
            related_user_id=approver_id,
            related_news_id=news_id,
            related_event_id=post.event_id
        )
    
    @staticmethod
    def notify_post_rejected(notification_db, auth_db, admin_db, news_id: int, rejector_id: int):
        """Notifica admin/patrocinador quando seu post é rejeitado (sempre envia, sem verificar preferências)"""
        from app.domain.admin.models.news_model import NewsPost
        from app.domain.admin.models.event_model import Event
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post or not post.author_id:
            return
        
        # Buscar o autor do post
        author = auth_db.query(User).filter(User.id == post.author_id).first()
        if not author:
            return
        
        # Só notifica se o autor for admin ou patrocinador
        if author.role not in ["admin", "patrocinador"]:
            return
        
        # Não notifica a si mesmo se o rejeitador for o próprio autor
        if post.author_id == rejector_id:
            return
        
        rejector = auth_db.query(User).filter(User.id == rejector_id).first()
        if not rejector:
            return
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == post.event_id).first()
        event_name = event.title if event else "evento"
        
        # Sempre cria notificação (sem verificar preferências)
        NotificationService.create_notification(
            notification_db,
            user_id=post.author_id,
            notification_type="post_rejected",
            title="Seu post não foi aprovado",
            message=f"Seu post do evento {event_name} foi rejeitado por {rejector.name}",
            related_user_id=rejector_id,
            related_news_id=news_id,
            related_event_id=post.event_id
        )
    
    @staticmethod
    def notify_post_deactivated(notification_db, auth_db, admin_db, news_id: int, deactivator_id: int):
        """Notifica admin/patrocinador quando seu post é desativado (sempre envia, sem verificar preferências)"""
        from app.domain.admin.models.news_model import NewsPost
        from app.domain.admin.models.event_model import Event
        
        post = admin_db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if not post or not post.author_id:
            return
        
        # Buscar o autor do post
        author = auth_db.query(User).filter(User.id == post.author_id).first()
        if not author:
            return
        
        # Só notifica se o autor for admin ou patrocinador
        if author.role not in ["admin", "patrocinador"]:
            return
        
        # Não notifica a si mesmo se o desativador for o próprio autor
        if post.author_id == deactivator_id:
            return
        
        deactivator = auth_db.query(User).filter(User.id == deactivator_id).first()
        if not deactivator:
            return
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == post.event_id).first()
        event_name = event.title if event else "evento"
        
        # Sempre cria notificação (sem verificar preferências)
        NotificationService.create_notification(
            notification_db,
            user_id=post.author_id,
            notification_type="post_deactivated",
            title="Seu post foi desativado",
            message=f"Seu post do evento {event_name} foi desativado por {deactivator.name}",
            related_user_id=deactivator_id,
            related_news_id=news_id,
            related_event_id=post.event_id
        )
    
    @staticmethod
    def notify_new_event(notification_db, auth_db, admin_db, event_id: int):
        """Notifica todos os usuários sobre um novo evento disponível"""
        from app.domain.admin.models.event_model import Event
        
        # Buscar o evento para incluir o nome na mensagem
        event = admin_db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return
        
        event_name = event.title
        
        # Buscar todos os usuários ativos
        all_users = auth_db.query(User).filter(User.status == "active").all()
        
        for user in all_users:
            # VERIFICAR PREFERÊNCIA
            preference = NotificationPreferenceRepository.get_or_create(notification_db, user.id)
            if preference.new_events:
                NotificationService.create_notification(
                    notification_db,
                    user_id=user.id,
                    notification_type="new_event",
                    title="Novo evento disponível!",
                    message=f"Novo evento: {event_name}",
                    related_event_id=event_id
                )
    
    @staticmethod
    def remove_event_notifications(notification_db, event_id: int):
        """Remove todas as notificações de novo evento relacionadas a um evento"""
        NotificationRepository.delete_by_event_id(notification_db, event_id, "new_event")
    
    @staticmethod
    def restore_event_notifications(notification_db, auth_db, admin_db, event_id: int):
        """Cria notificações de novo evento quando um evento é ativado"""
        from app.domain.admin.models.event_model import Event
        
        # Buscar o evento
        event = admin_db.query(Event).filter(Event.id == event_id).first()
        if not event or not event.is_active:
            return
        
        # Remove notificações antigas se existirem (para evitar duplicatas)
        NotificationRepository.delete_by_event_id(notification_db, event_id, "new_event")
        
        # Cria notificações para todos os usuários ativos
        event_name = event.title
        all_users = auth_db.query(User).filter(User.status == "active").all()
        
        for user in all_users:
            preference = NotificationPreferenceRepository.get_or_create(notification_db, user.id)
            if preference.new_events:
                NotificationService.create_notification(
                    notification_db,
                    user_id=user.id,
                    notification_type="new_event",
                    title="Novo evento disponível!",
                    message=f"Novo evento: {event_name}",
                    related_event_id=event_id
                )
    
    @staticmethod
    def broadcast_notification(notification_db, auth_db, title: str, message: str, sender_id: int):
        """Envia uma notificação para todos os usuários ativos do sistema"""
        # Buscar todos os usuários ativos
        all_users = auth_db.query(User).filter(User.status == "active").all()
        
        users_notified = 0
        for user in all_users:
            # Cria notificação para cada usuário (sem verificar preferências, pois é um broadcast administrativo)
            NotificationService.create_notification(
                notification_db,
                user_id=user.id,
                notification_type="admin_broadcast",
                title=title,
                message=message,
                broadcast_sender_id=sender_id
            )
            users_notified += 1
        
        return users_notified

