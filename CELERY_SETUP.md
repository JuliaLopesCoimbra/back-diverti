# Configuração do Celery para Notificações

## O que é Celery?

Celery é um sistema de filas distribuído que processa tarefas assíncronas em workers separados. Isso permite que o servidor FastAPI não seja sobrecarregado ao processar notificações.

## Arquitetura

```
FastAPI → Envia tarefa → Redis (fila) → Celery Worker → Processa notificação
```

## Instalação

O Celery já está no `requirements.txt`. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Configuração

O Celery está configurado em `app/infra/celery_app.py` e usa o Redis como broker.

### Variáveis de Ambiente

Certifique-se de que o Redis está configurado no `.env`:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Opcional
```

Ou use `REDIS_URL`:

```env
REDIS_URL=redis://localhost:6379/0
```

## Como Rodar

### 1. Iniciar Redis

```bash
# Linux/Mac
sudo systemctl start redis
# ou
redis-server

# Windows (Docker)
docker run -d -p 6379:6379 --name redis redis:latest
```

### 2. Iniciar Celery Worker

Na sua máquina virtual, rode:

```bash
# Comando básico
celery -A app.infra.celery_app worker --loglevel=info

# Com mais workers (recomendado para 10k usuários)
celery -A app.infra.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --hostname=worker1@%h

# Com múltiplos workers em processos separados
celery -A app.infra.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000
```

### 3. Rodar em Background (Produção)

#### Opção 1: Com nohup

```bash
nohup celery -A app.infra.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    > celery.log 2>&1 &
```

#### Opção 2: Com screen

```bash
screen -S celery
celery -A app.infra.celery_app worker --loglevel=info --concurrency=4
# Detachar: Ctrl+A depois D
# Reatachar: screen -r celery
```

#### Opção 3: Com systemd (Recomendado para produção)

Criar arquivo `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Celery worker for notifications
After=network.target redis.service

[Service]
Type=forking
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/back-n1
Environment="PATH=/home/ec2-user/.local/bin"
ExecStart=/home/ec2-user/.local/bin/celery -A app.infra.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/home/ec2-user/back-n1/celery.log \
    --pidfile=/home/ec2-user/back-n1/celery.pid \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Depois:

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
sudo systemctl status celery
```

## Verificar se está funcionando

### 1. Ver processos Celery

```bash
ps aux | grep celery
# Deve mostrar processos do worker
```

### 2. Ver logs

```bash
# Se rodou com nohup
tail -f celery.log

# Se rodou com systemd
sudo journalctl -u celery -f
```

### 3. Testar manualmente

```python
# No Python shell
from app.domain.users.tasks.notification_tasks import notify_post_like_task

# Enviar tarefa
result = notify_post_like_task.delay(1, 123)
print(result.id)  # ID da tarefa
print(result.status)  # PENDING, SUCCESS, FAILURE
```

## Monitoramento

### Flower (Interface Web - Opcional)

```bash
# Instalar
pip install flower

# Rodar
celery -A app.infra.celery_app flower --port=5555

# Acessar
# http://localhost:5555
```

### Verificar fila no Redis

```bash
redis-cli
> LLEN celery  # Ver tamanho da fila
> KEYS celery*  # Ver todas as chaves do Celery
```

## Tasks Disponíveis

- `notifications.notify_post_like` - Notificação de curtida de post
- `notifications.notify_post_comment` - Notificação de comentário no post
- `notifications.notify_comment_reply` - Notificação de resposta a comentário
- `notifications.notify_comment_like` - Notificação de curtida de comentário
- `notifications.remove_post_like_notification` - Remover notificação de curtida
- `notifications.remove_comment_like_notification` - Remover notificação de curtida de comentário

## Configurações

As configurações estão em `app/infra/celery_app.py`:

- **task_time_limit**: 30 minutos (tempo máximo para processar)
- **worker_prefetch_multiplier**: 4 (tarefas por worker)
- **worker_max_tasks_per_child**: 1000 (reinicia worker após 1000 tarefas)
- **max_retries**: 3 (tentativas automáticas em caso de erro)

## Troubleshooting

### Worker não processa tarefas

1. Verificar se Redis está rodando:
```bash
redis-cli ping
# Deve retornar: PONG
```

2. Verificar logs do worker:
```bash
tail -f celery.log
```

3. Verificar se há tarefas na fila:
```bash
redis-cli LLEN celery
```

### Tarefas falhando

1. Verificar logs de erro
2. Verificar conexões com bancos de dados
3. Verificar se todas as dependências estão instaladas

### Worker consumindo muita memória

Aumentar `worker_max_tasks_per_child` para reiniciar workers mais frequentemente:

```bash
celery -A app.infra.celery_app worker \
    --max-tasks-per-child=500 \
    --concurrency=4
```

## Performance

Para 10.000 usuários simultâneos:

- **Concurrency**: 4-8 workers
- **Prefetch**: 4 tarefas por worker
- **Max tasks per child**: 1000 (evita memory leaks)

## Próximos Passos

1. Configurar monitoramento (Flower ou similar)
2. Configurar alertas para filas cheias
3. Considerar múltiplos workers em servidores diferentes
4. Configurar retry policies mais sofisticadas

