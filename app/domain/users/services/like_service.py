from app.domain.users.repositories.like_repository import LikeRepository
from sqlalchemy.exc import IntegrityError
from app.infra.redis import redis_client, CacheKeys

class LikeService:

    @staticmethod
    def add_like(interaction_db, admin_db, news_id: int, user_id: int, ip_address: str = None, user_agent: str = None, background_tasks=None):
        try:
            LikeRepository.create(
                interaction_db,
                news_id,
                user_id,
                ip_address,
                user_agent,
                admin_db
            )
            
            # Invalidação de cache será feita em background (não bloqueia a resposta)
            # A invalidação é feita através do LikeController que recebe background_tasks
            
            # Notificações serão criadas em background (não bloqueia a resposta)
            # As notificações são criadas através do LikeController que recebe background_tasks
            
            return {
                "news_id": news_id,
                "liked": True,
                "message": "Post curtido"
            }

        except IntegrityError as e:
            # Se ainda houver constraint único (caso a migração não tenha sido executada),
            # verifica se já existe like ativo e retorna mensagem apropriada
            interaction_db.rollback()
            
            # Verifica se já existe um like ativo
            existing = LikeRepository.get_like(interaction_db, news_id, user_id)
            if existing:
                return {
                    "news_id": news_id,
                    "liked": True,
                    "message": "Post já curtido"
                }
            
            # Se não existe, re-lança o erro (pode ser outro problema)
            raise

    @staticmethod
    def get_likes_count(interaction_db, news_id: int) -> int:
        """Busca contagem de likes com cache"""
        cache_key = CacheKeys.likes_count(news_id)
        cached = redis_client.get(cache_key)
        if cached is not None:
            return cached
        
        count = LikeRepository.count_by_news(interaction_db, news_id)
        # Cacheia por 15 minutos (900 segundos) - cache mais agressivo devido à latência
        redis_client.set(cache_key, count, ttl=900)
        return count

    @staticmethod
    def remove_like(interaction_db, news_id: int, user_id: int, background_tasks=None):
        """Remove like e invalida cache"""
        removed = LikeRepository.remove(interaction_db, news_id, user_id)
        
        # Invalidação de cache será feita em background (não bloqueia a resposta)
        # A invalidação é feita através do LikeController que recebe background_tasks
        
        # Notificações serão removidas em background (não bloqueia a resposta)
        # As notificações são removidas através do LikeController que recebe background_tasks
        
        return {
            "news_id": news_id,
            "liked": False,
            "message": "Post descurtido" if removed else "Post já não estava curtido"
        }

    @staticmethod
    def get_liked_posts(admin_db, interaction_db, auth_db, user_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        """
        Retorna lista de notícias que o usuário curtiu com todos os detalhes, opcionalmente filtrado por evento.
        Otimizado para evitar N+1 queries usando batch loading.
        """
        # Importação local para evitar dependência circular
        from app.domain.admin.services.news_service import NewsService
        
        # Busca os IDs das notícias que o usuário curtiu (filtrado por evento se fornecido)
        liked_news_ids = LikeRepository.get_liked_news_ids(interaction_db, user_id, event_id, admin_db)
        
        if not liked_news_ids:
            return []
        
        # Aplica paginação nos IDs
        paginated_ids = liked_news_ids[offset:offset + limit]
        
        if not paginated_ids:
            return []
        
        # Busca os detalhes completos de todas as notícias de uma vez (otimizado)
        try:
            result = NewsService.get_multiple_news_with_details(
                admin_db, 
                interaction_db, 
                auth_db, 
                paginated_ids, 
                user_id
            )
            return result
        except Exception as e:
            # Em caso de erro, retorna lista vazia
            return []

    @staticmethod
    def get_users_who_liked(interaction_db, auth_db, news_id: int, limit: int = 10, offset: int = 0):
        """Retorna lista de usuários que curtiram uma notícia, com paginação."""
        return LikeRepository.get_users_who_liked(interaction_db, auth_db, news_id, limit, offset)