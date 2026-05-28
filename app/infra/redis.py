# app/infra/redis.py
import json
import redis
from typing import Optional, Any, Callable
from functools import wraps
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    """Cliente Redis singleton para cache e rate limiting"""
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                if settings.REDIS_URL:
                    self._client = redis.from_url(
                        settings.REDIS_URL,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                else:
                    self._client = redis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                # Testa conexão
                self._client.ping()
                print("✅ Redis conectado com sucesso")
            except Exception as e:
                print(f"⚠️  Redis não disponível: {e}")
                self._client = None
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Retorna o cliente Redis ou None se não conectado"""
        return self._client
    
    def is_connected(self) -> bool:
        """Verifica se Redis está conectado"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Busca valor do cache"""
        if not self.is_connected():
            return None
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar cache {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazena valor no cache"""
        if not self.is_connected():
            return False
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            serialized = json.dumps(value, default=str)
            return self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Erro ao salvar cache {key}: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Remove chaves do cache"""
        if not self.is_connected():
            return 0
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Erro ao deletar cache: {e}")
            return 0
    
    def delete_pattern(self, pattern: str) -> int:
        """Remove todas as chaves que correspondem ao padrão"""
        if not self.is_connected():
            return 0
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao deletar padrão {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe"""
        if not self.is_connected():
            return False
        try:
            return bool(self._client.exists(key))
        except:
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa valor (útil para rate limiting)"""
        if not self.is_connected():
            return None
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erro ao incrementar {key}: {e}")
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """Define TTL para uma chave"""
        if not self.is_connected():
            return False
        try:
            return bool(self._client.expire(key, ttl))
        except:
            return False


# Instância global
redis_client = RedisClient()


# ===== HELPERS PARA CHAVES DE CACHE =====

class CacheKeys:
    """Centraliza todas as chaves de cache"""
    
    @staticmethod
    def news_event(event_id: int, limit: int, offset: int) -> str:
        return f"news:event:{event_id}:limit:{limit}:offset:{offset}"
    
    @staticmethod
    def news_details(news_id: int, user_id: Optional[int] = None) -> str:
        user_part = f":user:{user_id}" if user_id else ""
        return f"news:details:{news_id}{user_part}"
    
    @staticmethod
    def event_details(event_id: int) -> str:
        return f"event:details:{event_id}"
    
    @staticmethod
    def events_list() -> str:
        return "events:list:active"
    
    @staticmethod
    def likes_count(news_id: int) -> str:
        return f"likes:count:{news_id}"
    
    @staticmethod
    def comments_count(news_id: int) -> str:
        return f"comments:count:{news_id}"
    
    @staticmethod
    def user_liked_posts(user_id: int, event_id: Optional[int] = None) -> str:
        event_part = f":event:{event_id}" if event_id else ""
        return f"user:liked:{user_id}{event_part}"
    
    @staticmethod
    def comments_list(news_id: int, user_id: Optional[int] = None) -> str:
        user_part = f":user:{user_id}" if user_id else ""
        return f"comments:list:{news_id}{user_part}"
    
    @staticmethod
    def user_me(user_id: int) -> str:
        return f"user:me:{user_id}"
    
    @staticmethod
    def roulette_event(event_id: int) -> str:
        return f"roulette:event:{event_id}"
    
    @staticmethod
    def prizes_event(event_id: int) -> str:
        return f"prizes:event:{event_id}"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:profile:{user_id}"


# ===== RATE LIMITING =====

def check_rate_limit(
    identifier: str, 
    max_requests: int, 
    window_seconds: int = 60,
    critical: bool = False
) -> tuple[bool, int]:
    """
    Verifica rate limit com fallback híbrido quando Redis não está disponível
    
    Args:
        identifier: Identificador único (ex: IP, user_id, email)
        max_requests: Número máximo de requisições permitidas
        window_seconds: Janela de tempo em segundos
        critical: Se True, retorna erro 503 se Redis cair (endpoints críticos).
                  Se False, permite com alerta (endpoints menos críticos).
    
    Returns:
        (allowed, remaining): Se a requisição é permitida e quantas restam
    
    Raises:
        HTTPException: Se critical=True e Redis não está disponível (503 Service Unavailable)
    """
    if not redis_client.is_connected():
        if critical:
            # Endpoints críticos: retornar erro 503 para forçar correção do Redis
            logger.critical(
                f"🚨 CRÍTICO: Redis não disponível - Rate limiting crítico indisponível para {identifier}",
                extra={
                    "identifier": identifier,
                    "max_requests": max_requests,
                    "window_seconds": window_seconds,
                    "severity": "CRITICAL",
                    "action": "rejecting_request"
                }
            )
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em alguns instantes.",
                headers={"Retry-After": "60"}
            )
        else:
            # Endpoints menos críticos: permitir com alerta
            logger.error(
                f"⚠️ Redis não disponível - Rate limiting desabilitado para {identifier}",
                extra={
                    "identifier": identifier,
                    "max_requests": max_requests,
                    "window_seconds": window_seconds,
                    "severity": "WARNING",
                    "action": "allowing_request"
                }
            )
            return True, max_requests
    
    # Redis está disponível - comportamento normal
    key = f"ratelimit:{identifier}:{window_seconds}"
    current = redis_client.increment(key)
    
    if current is None:
        # Erro ao incrementar (Redis pode ter caído durante a operação)
        if critical:
            logger.critical(f"Erro ao incrementar rate limit no Redis para {identifier}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em alguns instantes.",
                headers={"Retry-After": "60"}
            )
        else:
            logger.error(f"Erro ao incrementar rate limit no Redis para {identifier} - permitindo requisição")
            return True, max_requests
    
    if current == 1:
        # Primeira requisição, define TTL
        redis_client.expire(key, window_seconds)
    
    remaining = max(0, max_requests - current)
    allowed = current <= max_requests
    
    return allowed, remaining


def rate_limit_by_ip(max_requests: int, window_seconds: int = 60):
    """
    Decorador para rate limiting por IP
    
    Args:
        max_requests: Número máximo de requisições
        window_seconds: Janela de tempo em segundos
    """
    def decorator(func):
        from functools import wraps
        from fastapi import Request, HTTPException
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Tenta pegar request dos kwargs ou args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if request:
                ip = request.client.host
                identifier = f"ip:{ip}:{func.__name__}"
                allowed, remaining = check_rate_limit(identifier, max_requests, window_seconds)
                
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Muitas requisições. Tente novamente em {window_seconds} segundos.",
                        headers={"X-RateLimit-Remaining": "0", "Retry-After": str(window_seconds)}
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_by_user(max_requests: int, window_seconds: int = 60):
    """
    Decorador para rate limiting por usuário autenticado
    
    Args:
        max_requests: Número máximo de requisições
        window_seconds: Janela de tempo em segundos
    """
    def decorator(func):
        from functools import wraps
        from fastapi import HTTPException
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Tenta pegar user dos kwargs
            user = kwargs.get('user')
            
            if user and hasattr(user, 'id'):
                identifier = f"user:{user.id}:{func.__name__}"
                allowed, remaining = check_rate_limit(identifier, max_requests, window_seconds)
                
                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Muitas requisições. Tente novamente em {window_seconds} segundos.",
                        headers={"X-RateLimit-Remaining": "0", "Retry-After": str(window_seconds)}
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

