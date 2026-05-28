# Troubleshooting: Notificações não estão sendo criadas

## Problema: Notificações não aparecem após implementar Celery

### Diagnóstico Rápido

#### 1. Verificar se Celery Worker está rodando

```bash
# Na VM de produção
ps aux | grep celery

# Deve mostrar processos do worker. Se não mostrar, o worker não está rodando!
```

#### 2. Verificar se Redis está acessível

```bash
# Testar conexão
redis-cli ping
# Deve retornar: PONG

# Verificar se há tarefas na fila
redis-cli LLEN celery
# Se retornar número > 0, há tarefas esperando para serem processadas
```

#### 3. Verificar logs do Celery

```bash
# Se rodou com nohup
tail -f celery.log

# Se rodou com systemd
sudo journalctl -u celery -f

# Procurar por erros
grep -i error celery.log
```

#### 4. Verificar logs do Gunicorn/FastAPI

```bash
# Verificar se as tasks estão sendo enviadas
tail -f gunicorn.log | grep -i celery
```

## Soluções

### Problema 1: Celery Worker não está rodando

**Sintoma:** Tarefas ficam na fila mas nunca são processadas

**Solução:**
```bash
# Na VM, iniciar Celery
cd ~/back-n1
python -m celery -A app.infra.celery_app worker --loglevel=info --concurrency=4
```

### Problema 2: Redis não está acessível

**Sintoma:** Erro ao enviar tarefa para Celery

**Solução:**
```bash
# Verificar se Redis está rodando
sudo systemctl status redis

# Se não estiver, iniciar
sudo systemctl start redis
sudo systemctl enable redis
```

### Problema 3: Tasks estão falhando

**Sintoma:** Tarefas são recebidas mas falham ao processar

**Verificar logs:**
```bash
# Ver logs do Celery
tail -f celery.log

# Procurar por:
# - "Task ... failed"
# - "Error"
# - "Exception"
```

**Causas comuns:**
- Erro de conexão com banco de dados
- Erro na lógica de notificação
- Dados inválidos

### Problema 4: Tasks não estão sendo enviadas

**Verificar se o código está chamando:**
```python
# Deve estar assim:
notify_post_like_task.delay(news_id, user.id)

# NÃO assim:
notify_post_like_task(news_id, user.id)  # ❌ Errado - executa síncrono
```

### Problema 5: Task não registrada - "Received unregistered task"

**Sintoma:** Erro no log do Celery:
```
Received unregistered task of type 'notifications.broadcast_notification'.
The message has been ignored and discarded.
```

**Causa:** O worker do Celery precisa ser reiniciado após adicionar novas tasks.

**Solução:**
```bash
# 1. Parar o worker atual (Ctrl+C ou kill)
# Se estiver rodando como serviço systemd:
sudo systemctl restart celery

# 2. Ou se estiver rodando manualmente, parar e reiniciar:
# Parar: Ctrl+C ou kill <PID>
# Reiniciar:
cd ~/back-n1
python -m celery -A app.infra.celery_app worker --loglevel=info --concurrency=4

# 3. Verificar se todas as tasks estão registradas:
python -m celery -A app.infra.celery_app inspect registered
```

**Prevenção:** Sempre reiniciar o worker após adicionar novas tasks ao código.

## Teste Manual

### 1. Testar envio de tarefa

```python
# No Python shell
from app.domain.users.tasks.notification_tasks import notify_post_like_task

# Enviar tarefa
result = notify_post_like_task.delay(1, 123)
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

# Verificar resultado (aguardar alguns segundos)
import time
time.sleep(2)
print(f"Status após processar: {result.status}")
```

### 2. Verificar se task foi processada

```bash
# No terminal do Celery worker, você deve ver:
[INFO] Task notifications.notify_post_like[xxx] received
[INFO] Notificação de curtida de post criada: news_id=1, liker_id=123
[INFO] Task notifications.notify_post_like[xxx] succeeded
```

### 3. Verificar no banco de dados

```sql
-- Verificar se notificação foi criada
SELECT * FROM notifications 
WHERE type = 'post_like' 
ORDER BY created_at DESC 
LIMIT 10;
```

## Checklist de Verificação

- [ ] Redis está rodando (`redis-cli ping` retorna PONG)
- [ ] Celery worker está rodando (`ps aux | grep celery` mostra processos)
- [ ] Código está chamando `.delay()` (não a função diretamente)
- [ ] Logs do Celery não mostram erros
- [ ] Tarefas aparecem na fila do Redis (`redis-cli LLEN celery`)
- [ ] Banco de dados está acessível
- [ ] Variáveis de ambiente estão configuradas corretamente

## Fallback Temporário

Se o Celery não estiver funcionando, você pode temporariamente voltar a usar BackgroundTasks:

```python
# Comentar a linha do Celery
# notify_post_like_task.delay(news_id, user.id)

# Descomentar a linha antiga
from app.domain.users.services.notification_background import notify_post_like_async
background_tasks.add_task(notify_post_like_async, news_id, user.id)
```

Mas isso não é recomendado para produção com 10k usuários.

## Próximos Passos

1. Verificar se Celery está rodando na VM
2. Verificar logs para erros
3. Testar manualmente enviando uma tarefa
4. Verificar se notificações estão sendo criadas no banco

