from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.repositories.news_repository import NewsRepository
from app.domain.admin.models.news_model import NewsPost
from app.domain.users.services.like_service import LikeService
from app.domain.users.services.comment_service import CommentService
from app.domain.users.repositories.like_repository import LikeRepository
from app.infra.s3_upload import upload_image_to_s3, upload_news_images_to_s3
from app.infra.redis import redis_client, CacheKeys


class NewsService:

    @staticmethod
    def create_post(db, title, content, image_url, user):
        if user.role not in ["admin_master", "subadmin", "colunista"]:
            raise HTTPException(403, "Apenas colunistas, subadmins ou admin master podem postar notícias.")

        # Criando a notícia no banco de dados com todos os parâmetros
        # Nota: Este método parece ser legado, use create_news que tem suporte completo
        return NewsRepository.create(
            db=db,
            title=title,
            content=content,
            image_url=image_url,
            author_id=user.id,
            status="approved" if user.role in ["admin_master", "subadmin"] else "pending"
        )

    @staticmethod
    def list_posts(db, limit: int = 10, offset: int = 0):
        return NewsRepository.list_all(db, limit, offset)

    @staticmethod
    def update_post(db, news_id, title, content, image_files, user, replace_all=False):
        if user.role not in ["admin_master", "subadmin", "colunista"]:
            raise HTTPException(status_code=403, detail="Apenas colunistas, subadmins ou admin master podem editar notícias.")

        news = NewsRepository.get(db, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="Notícia não encontrada.")

        # Verifica se o admin é o autor da news
        if news.author_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode editar notícias que você criou."
            )

        # Se o post já está aprovado e o usuário é colunista, volta para pending
        if news.status == "approved" and user.role == "colunista":
            news.status = "pending"
            news.approved_by_id = None
            news.approved_at = None

        # Atualiza os campos da notícia
        news.title = title
        news.content = content

        # Se houver novas imagens
        if image_files and len(image_files) > 0:
            from app.domain.admin.models.news_image_model import NewsImage
            
            if replace_all:
                # Remove todas as imagens antigas e substitui pelas novas
                db.query(NewsImage).filter(NewsImage.news_id == news_id).delete()
                
                # Faz upload das novas imagens
                from app.infra.s3_upload import upload_news_images_to_s3
                image_urls = upload_news_images_to_s3(image_files, news_id, folder="news_photos")
                
                # Cria as novas imagens
                for index, image_url in enumerate(image_urls):
                    news_image = NewsImage(
                        news_id=news_id,
                        image_url=image_url,
                        image_order=index
                    )
                    db.add(news_image)
            else:
                # Adiciona às existentes
                existing_images_count = db.query(NewsImage).filter(NewsImage.news_id == news_id).count()
                
                # Verifica se o total não excede 5
                total_images = existing_images_count + len(image_files)
                if total_images > 5:
                    raise HTTPException(400, f"Máximo de 5 imagens permitidas por post. Você já tem {existing_images_count} imagem(ns) e está tentando adicionar {len(image_files)}.")
                
                # Faz upload das novas imagens na estrutura news_photos/{post_id}/
                from app.infra.s3_upload import upload_news_images_to_s3
                image_urls = upload_news_images_to_s3(image_files, news_id, folder="news_photos")
                
                # Adiciona as novas imagens mantendo a ordem (existentes primeiro, depois as novas)
                for index, image_url in enumerate(image_urls):
                    news_image = NewsImage(
                        news_id=news_id,
                        image_url=image_url,
                        image_order=existing_images_count + index
                    )
                    db.add(news_image)

        # Força o flush para garantir que as mudanças sejam enviadas ao banco
        db.flush()
        db.commit()
        db.refresh(news)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{news.event_id}:*")
        redis_client.delete_pattern("news:details:*")
        
        return news

    # Adicionando o método de deletação (soft delete)
    @staticmethod
    def delete_post(db, news_id, user):
        if user.role not in ["admin_master", "subadmin", "colunista"]:
            raise HTTPException(status_code=403, detail="Apenas colunistas, subadmins ou admin master podem deletar notícias.")

        news = NewsRepository.get(db, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="Notícia não encontrada.")

        # Verifica se o post já foi deletado
        if news.status == "deleted" or news.deleted_at is not None:
            raise HTTPException(status_code=400, detail="Post já foi deletado.")

        # Verifica se o admin é o autor da news
        if news.author_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Você só pode deletar notícias que você criou."
            )

        # Soft delete: marca como deletado sem remover do banco
        news.status = "deleted"
        news.deleted_at = datetime.utcnow()
        news.deleted_by_id = user.id
        
        db.commit()
        db.refresh(news)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{news.event_id}:*")
        redis_client.delete_pattern("news:details:*")
        redis_client.delete(CacheKeys.likes_count(news_id))
        redis_client.delete(CacheKeys.comments_count(news_id))
        
        # Remove notificações relacionadas a este post
        try:
            from app.config.notification_db import get_notification_db
            from app.domain.users.services.notification_service import NotificationService
            notification_db = next(get_notification_db())
            try:
                NotificationService.remove_post_notifications(notification_db, news_id)
            finally:
                notification_db.close()
        except Exception as e:
            # Não quebra o fluxo se a remoção de notificações falhar
            print(f"Erro ao remover notificações de post deletado: {e}")
        
        return news

    # Método para buscar uma notícia pelo ID
    @staticmethod
    def get_post(db, id):
        return NewsRepository.get(db, id)

    @staticmethod
    def create_news(db, data, user, image_files=None):
        """Colunistas, subadmins e admin_master podem criar posts"""
        if user.role not in ["admin_master", "subadmin", "colunista"]:
            raise HTTPException(403, "Apenas colunistas, subadmins ou admin master podem criar posts.")

        event = EventRepository.get_by_id(db, data["event_id"])
        if not event:
            raise HTTPException(404, "Evento não encontrado")

        # Verificar se o evento requer aprovação
        requires_approval = getattr(event, 'requires_post_approval', True)
        
        # Se for admin_master ou subadmin, não precisa aprovação
        if user.role in ["admin_master", "subadmin"]:
            status = "approved"
            approved_by_id = user.id
        elif requires_approval:
            status = "pending"
            approved_by_id = None
        else:
            status = "approved"
            approved_by_id = None
        
        # Adicionar campos de aprovação ao data
        data["status"] = status
        data["approved_by_id"] = approved_by_id
        data["requires_approval"] = requires_approval
        if status == "approved":
            data["approved_at"] = datetime.utcnow()

        # Criar o post primeiro para obter o ID
        news_data = {k: v for k, v in data.items() if k != 'image_urls'}
        news = NewsPost(**news_data)
        db.add(news)
        db.flush()  # Para obter o ID antes do commit
        
        # Upload das imagens se houver
        image_urls = []
        if image_files and len(image_files) > 0:
            if len(image_files) > 5:
                raise HTTPException(400, "Máximo de 5 imagens permitidas por post.")
            
            # Faz upload das imagens na estrutura news_photos/{post_id}/
            image_urls = upload_news_images_to_s3(image_files, news.id, folder="news_photos")
        
        # Cria as imagens associadas
        if image_urls:
            from app.domain.admin.models.news_image_model import NewsImage
            for index, image_url in enumerate(image_urls):
                news_image = NewsImage(
                    news_id=news.id,
                    image_url=image_url,
                    image_order=index
                )
                db.add(news_image)
        
        db.commit()
        db.refresh(news)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{data['event_id']}:*")
        redis_client.delete_pattern("news:details:*")
        redis_client.delete_pattern("events:list:*")
        
        # Criar notificação se o post foi aprovado automaticamente via Celery
        if status == "approved":
            try:
                from app.domain.users.tasks.notification_tasks import notify_new_post_task
                notify_new_post_task.delay(news.id, data['event_id'])
            except Exception as e:
                # Não quebra o fluxo se a notificação falhar
                print(f"Erro ao enviar notificação de novo post para Celery: {e}")
        
        return news

    @staticmethod
    def approve_post(db, post_id, approver):
        """Apenas admin_master e subadmin podem aprovar posts"""
        if approver.role not in ["admin_master", "subadmin"]:
            raise HTTPException(403, "Apenas subadmins ou admin master podem aprovar posts.")
        
        post = NewsRepository.get(db, post_id)
        if not post:
            raise HTTPException(404, "Post não encontrado.")
        
        if post.status == "approved":
            raise HTTPException(400, "Post já está aprovado.")
        
        post.status = "approved"
        post.approved_by_id = approver.id
        post.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(post)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{post.event_id}:*")
        redis_client.delete_pattern("news:details:*")
        redis_client.delete_pattern("events:list:*")
        
        # Criar notificação quando um post é aprovado via Celery
        try:
            from app.config.notification_db import get_notification_db
            from app.config.auth_db import get_db as get_auth_db
            from app.domain.users.services.notification_service import NotificationService
            from app.domain.users.tasks.notification_tasks import notify_new_post_task
            
            # Notificar o autor que o post foi aprovado (para usuários comuns) - síncrono pois é rápido
            notification_db = next(get_notification_db())
            auth_db = next(get_auth_db())
            try:
                NotificationService.notify_post_approved(
                    notification_db, auth_db, db, post.id, approver.id
                )
                # Notificar subadmin/colunista que o post foi aprovado (sempre envia)
                NotificationService.notify_post_approved_admin(
                    notification_db, auth_db, db, post.id, approver.id
                )
            finally:
                notification_db.close()
                auth_db.close()
            
            # Notificar todos sobre o novo post publicado via Celery
            notify_new_post_task.delay(post.id, post.event_id)
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao enviar notificação de aprovação para Celery: {e}")
        
        return post

    @staticmethod
    def reject_post(db, post_id, rejector):
        """Apenas admin_master e subadmin podem rejeitar posts"""
        if rejector.role not in ["admin_master", "subadmin"]:
            raise HTTPException(403, "Apenas subadmins ou admin master podem rejeitar posts.")
        
        post = NewsRepository.get(db, post_id)
        if not post:
            raise HTTPException(404, "Post não encontrado.")
        
        from datetime import datetime
        post.status = "rejected"
        post.rejected_by_id = rejector.id
        post.rejected_at = datetime.utcnow()
        db.commit()
        db.refresh(post)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{post.event_id}:*")
        redis_client.delete_pattern("news:details:*")
        
        # Criar notificação quando um post é rejeitado
        try:
            from app.config.notification_db import get_notification_db
            from app.config.auth_db import get_db as get_auth_db
            from app.domain.users.services.notification_service import NotificationService
            notification_db = next(get_notification_db())
            auth_db = next(get_auth_db())
            try:
                # Notificar subadmin/colunista que o post foi rejeitado (sempre envia)
                NotificationService.notify_post_rejected(
                    notification_db, auth_db, db, post.id, rejector.id
                )
            finally:
                notification_db.close()
                auth_db.close()
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao criar notificação de rejeição: {e}")
        
        return post

    @staticmethod
    def deactivate_post(db, post_id, deactivator):
        """Apenas admin_master e subadmin podem desativar posts"""
        if deactivator.role not in ["admin_master", "subadmin"]:
            raise HTTPException(403, "Apenas subadmins ou admin master podem desativar posts.")
        
        post = NewsRepository.get(db, post_id)
        if not post:
            raise HTTPException(404, "Post não encontrado.")
        
        from datetime import datetime
        post.status = "rejected"
        post.rejected_by_id = deactivator.id
        post.rejected_at = datetime.utcnow()
        db.commit()
        db.refresh(post)
        
        # Invalida cache relacionado
        redis_client.delete_pattern(f"news:event:{post.event_id}:*")
        redis_client.delete_pattern("news:details:*")
        
        # Criar notificação quando um post é desativado
        try:
            from app.config.notification_db import get_notification_db
            from app.config.auth_db import get_db as get_auth_db
            from app.domain.users.services.notification_service import NotificationService
            notification_db = next(get_notification_db())
            auth_db = next(get_auth_db())
            try:
                # Notificar subadmin/colunista que o post foi desativado (sempre envia)
                NotificationService.notify_post_deactivated(
                    notification_db, auth_db, db, post.id, deactivator.id
                )
            finally:
                notification_db.close()
                auth_db.close()
        except Exception as e:
            # Não quebra o fluxo se a notificação falhar
            print(f"Erro ao criar notificação de desativação: {e}")
        
        return post

    @staticmethod
    def list_posts_for_approval(db, approver, event_id: int = None, limit: int = 10, offset: int = 0):
        """Lista posts pendentes de aprovação, opcionalmente filtrados por evento"""
        if approver.role not in ["admin_master", "subadmin"]:
            raise HTTPException(403, "Apenas subadmins ou admin master podem ver posts pendentes.")
        
        return NewsRepository.list_pending(db, limit=limit, offset=offset, event_id=event_id)

    @staticmethod
    def list_rejected_by_rejector(db, rejector, event_id: int = None, limit: int = 10, offset: int = 0):
        """Lista posts rejeitados por um admin/subadmin específico"""
        if rejector.role not in ["admin_master", "subadmin"]:
            raise HTTPException(403, "Apenas subadmins ou admin master podem ver posts rejeitados por eles.")
        
        return NewsRepository.list_rejected_by_rejector(db, rejector.id, event_id, limit, offset)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 10, offset: int = 0, include_pending: bool = False):
        """Lista posts de um evento. Por padrão, apenas aprovados. Com cache."""
        # Não cacheia se incluir pendentes (dados dinâmicos)
        if include_pending:
            posts = NewsRepository.list_by_event(db, event_id, limit, offset)
        else:
            # Cache apenas para posts aprovados
            cache_key = CacheKeys.news_event(event_id, limit, offset)
            cached = redis_client.get(cache_key)
            if cached is not None:
                return cached
            
            posts = NewsRepository.list_approved_by_event(db, event_id, limit, offset)
        
        # Busca informações dos autores de uma vez (otimização para evitar N+1)
        author_ids = {post.author_id for post in posts if post.author_id}
        authors_dict = {}
        if author_ids:
            from app.config.admin_db import AuthSessionLocal
            from app.domain.auth.models.user_model import User
            # Precisamos de uma sessão do auth_db para buscar os usuários
            auth_db = AuthSessionLocal()
            try:
                authors = (
                    auth_db.query(User)
                    .filter(User.id.in_(author_ids))
                    .all()
                )
                authors_dict = {author.id: author for author in authors}
            finally:
                auth_db.close()
        
        # Formata a resposta com informações do autor
        result = []
        for post in posts:
            images = [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "image_order": img.image_order
                }
                for img in sorted(post.images, key=lambda x: x.image_order) if post.images
            ] if post.images else []
            
            author = authors_dict.get(post.author_id) if post.author_id else None
            
            result.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "images": images,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "approved_at": post.approved_at.isoformat() if post.approved_at else None,
                "deleted_at": post.deleted_at.isoformat() if post.deleted_at else None,
                "deleted_by_id": post.deleted_by_id,
                "event_id": post.event_id,
                "status": post.status,
                "author": {
                    "id": author.id if author else None,
                    "name": author.name if author else None,
                    "profile_photo": author.profile_photo if author else None
                } if author else None
            })
        
        # Cacheia apenas para posts aprovados
        if not include_pending:
            cache_key = CacheKeys.news_event(event_id, limit, offset)
            redis_client.set(cache_key, result, ttl=300)
        
        return result

    @staticmethod
    def list_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsRepository.list_by_author(db, author_id, event_id, limit, offset)

    @staticmethod
    def list_pending_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsRepository.list_pending_by_author(db, author_id, event_id, limit, offset)

    @staticmethod
    def get_news_with_details(admin_db, interaction_db, auth_db, news_id: int, user_id: int = None):
        """
        Busca uma news completa com todas as informações:
        - Dados da news
        - Quantidade de curtidas
        - Se o usuário curtiu (se user_id fornecido)
        - Lista de comentários com informações dos usuários
        Com cache.
        """
        # Tenta buscar do cache
        cache_key = CacheKeys.news_details(news_id, user_id)
        cached = redis_client.get(cache_key)
        if cached is not None:
            return cached
        
        # Busca a news
        news = NewsRepository.get(admin_db, news_id)
        if not news:
            raise HTTPException(status_code=404, detail="Notícia não encontrada.")

        # OTIMIZAÇÃO: Combina busca de likes_count e user_liked em uma única query
        from app.domain.users.models.like_model import Like
        from sqlalchemy import func, case
        
        if user_id:
            # OTIMIZAÇÃO: Busca count e user_liked em UMA única query usando CASE
            # IMPORTANTE: Filtra apenas likes ativos (is_active = True)
            result = (
                interaction_db.query(
                    func.count(Like.id).label('total'),
                    func.max(
                        case(
                            (Like.user_id == user_id, 1),
                            else_=0
                        )
                    ).label('user_liked_flag')
                )
                .filter(Like.news_id == news_id, Like.is_active == True)
                .first()
            )
            likes_count = result.total if result and result.total else 0
            user_liked = bool(result.user_liked_flag) if result else False
        else:
            # Se não tem user_id, busca apenas o count (usa cache)
            likes_count = LikeService.get_likes_count(interaction_db, news_id)
            user_liked = False

        # Busca apenas os primeiros 20 comentários (otimização de performance)
        # O frontend pode carregar mais via paginação se necessário
        INITIAL_COMMENTS_LIMIT = 20
        comments = CommentService.list_comments(interaction_db, news_id, auth_db, user_id, limit=INITIAL_COMMENTS_LIMIT, offset=0)

        # Busca o total de comentários de forma eficiente (sem carregar todos)
        # Passa auth_db para contar apenas comentários de usuários que ainda existem
        from app.domain.users.repositories.comment_repository import CommentRepository
        total_comments_count = CommentRepository.count_main_comments(interaction_db, news_id, auth_db)

        # Busca informações do autor (se necessário) - otimizado: busca apenas campos necessários
        author = None
        if news.author_id:
            from app.domain.auth.models.user_model import User
            author_result = auth_db.query(User.id, User.name, User.profile_photo).filter(User.id == news.author_id).first()
            if author_result:
                author = {
                    "id": author_result[0],
                    "name": author_result[1],
                    "profile_photo": author_result[2]
                }

        # Monta o retorno
        images = [
            {
                "id": img.id,
                "image_url": img.image_url,
                "image_order": img.image_order
            }
            for img in sorted(news.images, key=lambda x: x.image_order) if news.images
        ] if news.images else []
        
        result = {
            "id": news.id,
            "title": news.title,
            "content": news.content,
            "images": images,
            "event_id": news.event_id,
            "status": news.status,
            "created_at": news.created_at.isoformat() if news.created_at else None,
            "updated_at": news.updated_at.isoformat() if news.updated_at else None,
            "approved_at": news.approved_at.isoformat() if news.approved_at else None,
            "approved_by_id": news.approved_by_id,
            "deleted_at": news.deleted_at.isoformat() if news.deleted_at else None,
            "deleted_by_id": news.deleted_by_id,
            "author": author,
            "likes": {
                "count": likes_count,
                "user_liked": user_liked
            },
            "comments": comments,
            "comments_count": total_comments_count  # Total real, não apenas os carregados
        }
        
        # Cacheia resultado por 30 minutos (1800 segundos) - cache mais agressivo devido à latência
        redis_client.set(cache_key, result, ttl=1800)
        
        return result

    @staticmethod
    def get_multiple_news_with_details(admin_db, interaction_db, auth_db, news_ids: list[int], user_id: int = None):
        """
        Busca múltiplas notícias com todas as informações de uma vez (otimizado para evitar N+1 queries).
        - Dados das news
        - Quantidade de curtidas (batch)
        - Se o usuário curtiu (batch)
        - Contagem de comentários (batch)
        - Informações dos autores (batch)
        """
        if not news_ids:
            return []
        
        # 1. Busca todas as notícias de uma vez
        news_list = (
            admin_db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.id.in_(news_ids),
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .all()
        )
        
        if not news_list:
            return []
        
        # Cria um dicionário para acesso rápido por ID
        news_dict = {news.id: news for news in news_list}
        found_ids = set(news_dict.keys())
        
        # 2. Busca contagens de likes de todas as notícias de uma vez
        # IMPORTANTE: Filtra apenas likes ativos (is_active = True)
        from app.domain.users.models.like_model import Like
        likes_counts = (
            interaction_db.query(Like.news_id, func.count(Like.id).label('count'))
            .filter(Like.news_id.in_(found_ids), Like.is_active == True)
            .group_by(Like.news_id)
            .all()
        )
        likes_count_dict = {news_id: count for news_id, count in likes_counts}
        
        # 3. Busca todos os likes do usuário de uma vez (se autenticado)
        # IMPORTANTE: Filtra apenas likes ativos (is_active = True)
        user_liked_set = set()
        if user_id:
            user_likes = (
                interaction_db.query(Like.news_id)
                .filter(
                    Like.news_id.in_(found_ids),
                    Like.user_id == user_id,
                    Like.is_active == True
                )
                .all()
            )
            user_liked_set = {like[0] for like in user_likes}
        
        # 4. Busca contagens de comentários de todas as notícias de uma vez
        from app.domain.users.models.comment_model import Comment
        comments_counts = (
            interaction_db.query(Comment.news_id, func.count(Comment.id).label('count'))
            .filter(
                Comment.news_id.in_(found_ids),
                Comment.deleted_at.is_(None)
            )
            .group_by(Comment.news_id)
            .all()
        )
        comments_count_dict = {news_id: count for news_id, count in comments_counts}
        
        # 5. Busca todos os autores de uma vez
        author_ids = {news.author_id for news in news_list if news.author_id}
        authors_dict = {}
        if author_ids:
            from app.domain.auth.models.user_model import User
            authors = (
                auth_db.query(User)
                .filter(User.id.in_(author_ids))
                .all()
            )
            authors_dict = {author.id: author for author in authors}
        
        # 6. Monta o resultado para cada notícia
        result = []
        for news_id in news_ids:  # Mantém a ordem original
            if news_id not in news_dict:
                continue
            
            news = news_dict[news_id]
            
            # Processa imagens
            images = [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "image_order": img.image_order
                }
                for img in sorted(news.images, key=lambda x: x.image_order) if news.images
            ] if news.images else []
            
            # Busca autor
            author = authors_dict.get(news.author_id) if news.author_id else None
            
            # Busca comentários completos (ainda precisa ser individual, mas pelo menos a contagem está otimizada)
            comments = CommentService.list_comments(interaction_db, news_id, auth_db, user_id)
            
            result.append({
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "images": images,
                "event_id": news.event_id,
                "status": news.status,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "updated_at": news.updated_at.isoformat() if news.updated_at else None,
                "approved_at": news.approved_at.isoformat() if news.approved_at else None,
                "approved_by_id": news.approved_by_id,
                "deleted_at": news.deleted_at.isoformat() if news.deleted_at else None,
                "deleted_by_id": news.deleted_by_id,
                "author": {
                    "id": author.id if author else None,
                    "name": author.name if author else None,
                    "profile_photo": author.profile_photo if author else None
                } if author else None,
                "likes": {
                    "count": likes_count_dict.get(news_id, 0),
                    "user_liked": news_id in user_liked_set
                },
                "comments": comments,
                "comments_count": comments_count_dict.get(news_id, 0)
            })
        
        return result