"""
Locustfile para testes de estresse da API N1
Execute com: locust -f locustfile.py --host=https://seu-backend-url.com
"""

from locust import HttpUser, task, between, events
import random
import json
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# IDs de teste (ajuste conforme seus dados reais)
TEST_EVENT_IDS = [1, 2, 3, 4, 5]  # IDs de eventos existentes
TEST_NEWS_IDS = [10, 11, 12, 13, 56,57,58,59,60]    # IDs de notícias existentes
TEST_COMMENT_IDS = [1, 2, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 3, 30, 32, 8, 33, 36, 35, 34, 37, 38, 39, 40, 41, 31, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 77, 76, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 116, 115, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140]
      # IDs de comentários existentes


class PublicUser(HttpUser):
    """
    Usuário não autenticado - testa endpoints públicos
    """
    wait_time = between(1, 3)
    weight = 3  # 30% dos usuários virtuais
    
    @task(10)
    def get_public_events(self):
        """Endpoint mais acessado - listar eventos públicos"""
        limit = random.choice([10, 20, 50])
        offset = random.randint(0, 100)
        self.client.get(
            f"/public/events?limit={limit}&offset={offset}",
            name="GET /public/events"
        )
    
    @task(5)
    def get_event_by_id(self):
        """Buscar evento específico"""
        event_id = random.choice(TEST_EVENT_IDS)
        self.client.get(
            f"/public/events/{event_id}",
            name="GET /public/events/{id}"
        )
    
    @task(3)
    def get_lineup_items(self):
        """Buscar itens do lineup"""
        event_id = random.choice(TEST_EVENT_IDS)
        self.client.get(
            f"/public/events/{event_id}/lineup-items",
            name="GET /public/events/{id}/lineup-items"
        )
    
    @task(2)
    def health_check(self):
        """Health check"""
        self.client.get("/", name="GET /")
    
    @task(1)
    def get_roulette(self):
        """Buscar roleta de um evento"""
        event_id = random.choice(TEST_EVENT_IDS)
        self.client.get(
            f"/roulette/events/{event_id}",
            name="GET /roulette/events/{id}"
        )


class AuthenticatedUser(HttpUser):
    """
    Usuário autenticado - testa endpoints que requerem login
    """
    wait_time = between(1, 4)
    weight = 7  # 70% dos usuários virtuais
    
    def on_start(self):
        """Login ao iniciar o usuário virtual"""
        # Ajuste estas credenciais para um usuário de teste real
        login_data = {
            "email": "teste@teste.com",  # ⚠️ AJUSTE: Use um email real
            "password": "senha123"       # ⚠️ AJUSTE: Use uma senha real
        }
        
        response = self.client.post(
            "/auth/login",
            json=login_data,
            name="POST /auth/login"
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.user_id = None  # Pode extrair do token se necessário
            except:
                self.token = None
                self.headers = {}
                logger.warning("Falha ao obter token de autenticação")
        else:
            self.token = None
            self.headers = {}
            logger.warning(f"Login falhou: {response.status_code}")
    
    # ===== PROFILE & AUTH =====
    @task(5)
    def get_profile(self):
        """Buscar perfil do usuário"""
        if self.token:
            self.client.get(
                "/user/profile",
                headers=self.headers,
                name="GET /user/profile"
            )
    
    @task(3)
    def get_me(self):
        """Endpoint /auth/me com cache"""
        if self.token:
            self.client.get(
                "/auth/me",
                headers=self.headers,
                name="GET /auth/me"
            )
    
    # ===== NEWS & INTERACTIONS =====
    @task(8)
    def get_news_details(self):
        """Buscar detalhes de uma notícia (endpoint mais pesado)"""
        news_id = random.choice(TEST_NEWS_IDS)
        self.client.get(
            f"/news/{news_id}/details",
            headers=self.headers if self.token else {},
            name="GET /news/{id}/details"
        )
    
    @task(6)
    def list_comments(self):
        """Listar comentários de uma notícia"""
        news_id = random.choice(TEST_NEWS_IDS)
        limit = random.choice([10, 20, 50])
        offset = random.randint(0, 50)
        self.client.get(
            f"/news/{news_id}/comments?limit={limit}&offset={offset}",
            headers=self.headers if self.token else {},
            name="GET /news/{id}/comments"
        )
    
    @task(4)
    def like_news(self):
        """Curtir uma notícia"""
        if self.token:
            news_id = random.choice(TEST_NEWS_IDS)
            self.client.post(
                f"/news/{news_id}/likes",
                headers=self.headers,
                name="POST /news/{id}/likes"
            )
    
    @task(3)
    def get_likes_count(self):
        """Contar curtidas de uma notícia"""
        news_id = random.choice(TEST_NEWS_IDS)
        self.client.get(
            f"/news/{news_id}/likes/count",
            name="GET /news/{id}/likes/count"
        )
    
    @task(2)
    def create_comment(self):
        """Criar comentário (rate limited)"""
        if self.token:
            news_id = random.choice(TEST_NEWS_IDS)
            comments = [
                "Ótima notícia!",
                "Muito interessante!",
                "Concordo totalmente!",
                "Excelente conteúdo!"
            ]
            self.client.post(
                f"/news/{news_id}/comments",
                params={"content": random.choice(comments)},
                headers=self.headers,
                name="POST /news/{id}/comments"
            )
    
    @task(2)
    def like_comment(self):
        """Curtir um comentário"""
        if self.token:
            comment_id = random.choice(TEST_COMMENT_IDS)
            self.client.post(
                f"/news/comments/{comment_id}/likes",
                headers=self.headers,
                name="POST /news/comments/{id}/likes"
            )
    
    # ===== ROULETTE =====
    @task(3)
    def get_roulette(self):
        """Buscar roleta de um evento"""
        event_id = random.choice(TEST_EVENT_IDS)
        self.client.get(
            f"/roulette/events/{event_id}",
            headers=self.headers if self.token else {},
            name="GET /roulette/events/{id}"
        )
    
    @task(1)
    def spin_roulette(self):
        """Girar roleta (rate limited - 10 por hora)"""
        if self.token:
            event_id = random.choice(TEST_EVENT_IDS)
            self.client.post(
                f"/roulette/events/{event_id}/spin",
                headers=self.headers,
                name="POST /roulette/events/{id}/spin"
            )
    
    # ===== NOTIFICATIONS =====
    @task(4)
    def list_notifications(self):
        """Listar notificações"""
        if self.token:
            limit = random.choice([10, 20])
            offset = random.randint(0, 20)
            unread_only = random.choice([True, False])
            self.client.get(
                f"/notifications?limit={limit}&offset={offset}&unread_only={unread_only}",
                headers=self.headers,
                name="GET /notifications"
            )
    
    @task(3)
    def get_unread_count(self):
        """Contar notificações não lidas"""
        if self.token:
            self.client.get(
                "/notifications/unread/count",
                headers=self.headers,
                name="GET /notifications/unread/count"
            )
    
    @task(1)
    def mark_notification_read(self):
        """Marcar notificação como lida"""
        if self.token:
            # Usar um ID de notificação real se disponível
            notification_id = random.randint(1, 100)
            self.client.patch(
                f"/notifications/{notification_id}/read",
                headers=self.headers,
                name="PATCH /notifications/{id}/read"
            )
    
    # ===== PUBLIC EVENTS (também acessados por usuários autenticados) =====
    @task(5)
    def get_public_events(self):
        """Listar eventos públicos"""
        limit = random.choice([10, 20, 50])
        offset = random.randint(0, 100)
        self.client.get(
            f"/public/events?limit={limit}&offset={offset}",
            headers=self.headers if self.token else {},
            name="GET /public/events (auth)"
        )


class AdminUser(HttpUser):
    """
    Usuário admin - testa endpoints administrativos
    Use com cuidado em produção!
    """
    wait_time = between(2, 5)
    weight = 0  # Desabilitado por padrão - ajuste para 1 se quiser testar
    
    def on_start(self):
        """Login como admin"""
        login_data = {
            "email": "admin@teste.com",  # ⚠️ AJUSTE: Use credenciais de admin
            "password": "admin123"       # ⚠️ AJUSTE: Use senha real
        }
        
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def list_news(self):
        """Listar notícias (admin)"""
        if self.token:
            self.client.get(
                "/admin/news?limit=20&offset=0",
                headers=self.headers,
                name="GET /admin/news (admin)"
            )


# ===== EVENT HANDLERS =====
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado quando o teste inicia"""
    print("\n" + "="*60)
    print("🚀 TESTE DE ESTRESSE INICIADO")
    print("="*60)
    print(f"Host: {environment.host}")
    print(f"Usuários: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado quando o teste termina"""
    print("\n" + "="*60)
    print("✅ TESTE DE ESTRESSE FINALIZADO")
    print("="*60)
    
    stats = environment.stats
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"Total de requisições: {stats.total.num_requests}")
    print(f"Total de falhas: {stats.total.num_failures}")
    print(f"Taxa de falhas: {(stats.total.num_failures / stats.total.num_requests * 100):.2f}%")
    print(f"RPS médio: {stats.total.total_rps:.2f}")
    print(f"Tempo médio de resposta: {stats.total.avg_response_time:.0f}ms")
    print(f"Tempo p95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"Tempo p99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print("="*60 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Monitora requisições individuais (opcional)"""
    if exception:
        logger.error(f"Erro em {name}: {exception}")


# ===== CONFIGURAÇÕES =====
"""
INSTRUÇÕES DE USO:

1. Instalar Locust:
   pip install locust

2. Ajustar configurações:
   - TEST_EVENT_IDS: IDs reais de eventos no banco
   - TEST_NEWS_IDS: IDs reais de notícias no banco
   - Credenciais de login nos métodos on_start()

3. Executar com interface web (recomendado):
   locust -f locustfile.py --host=https://seu-backend-url.com
   
   Acesse: http://localhost:8089

4. Executar headless (sem interface):
   locust -f locustfile.py \
       --host=https://seu-backend-url.com \
       --users 100 \
       --spawn-rate 10 \
       --run-time 5m \
       --headless

5. Executar distribuído (múltiplas máquinas):
   # Máquina master:
   locust -f locustfile.py --master --host=https://seu-backend-url.com
   
   # Máquinas workers:
   locust -f locustfile.py --worker --master-host=<IP_MASTER>

CENÁRIOS DE TESTE SUGERIDOS:

1. Teste Leve (baseline):
   - 10 usuários, spawn-rate 2, 2 minutos
   
2. Teste Moderado:
   - 50 usuários, spawn-rate 5, 5 minutos
   
3. Teste Pesado:
   - 100 usuários, spawn-rate 10, 10 minutos
   
4. Teste Extremo:
   - 200+ usuários, spawn-rate 20, 15 minutos

MÉTRICAS IMPORTANTES:
- Taxa de erro < 1%
- Tempo p95 < 500ms (endpoints leves)
- Tempo p95 < 2000ms (endpoints pesados)
- RPS sustentável conforme capacidade do servidor
"""