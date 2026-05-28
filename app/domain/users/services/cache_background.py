"""Serviço para invalidar cache em background (não bloqueia a resposta da API)"""
from app.infra.redis import redis_client, CacheKeys

def invalidate_comment_cache_async(news_id: int, user_id: int = None):
    """Invalida cache relacionado a comentários em background"""
    try:
        if redis_client.is_connected():
            # Remove chaves específicas primeiro (mais rápido)
            redis_client.delete(CacheKeys.comments_count(news_id))
            redis_client.delete(CacheKeys.comments_list(news_id, None))
            if user_id:
                redis_client.delete(CacheKeys.comments_list(news_id, user_id))
            redis_client.delete(CacheKeys.news_details(news_id, None))
            if user_id:
                redis_client.delete(CacheKeys.news_details(news_id, user_id))
            
            # Remove padrões (pode ser mais lento, mas em background não importa)
            redis_client.delete_pattern(f"comments:list:{news_id}:*")
            redis_client.delete_pattern(f"news:details:{news_id}:*")
    except Exception as e:
        print(f"Erro ao invalidar cache de comentários em background: {e}")

def invalidate_like_cache_async(news_id: int, user_id: int = None):
    """Invalida cache relacionado a likes em background"""
    try:
        if redis_client.is_connected():
            redis_client.delete(CacheKeys.likes_count(news_id))
            if user_id:
                redis_client.delete_pattern(f"user:liked:{user_id}:*")
            redis_client.delete_pattern(f"news:details:{news_id}:*")
    except Exception as e:
        print(f"Erro ao invalidar cache de likes em background: {e}")














