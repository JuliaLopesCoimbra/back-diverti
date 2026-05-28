# Como Rodar Celery no Windows

## ⚠️ Problema no Windows

No Windows, o Celery **não suporta** o pool `prefork` (padrão). Você precisa usar `--pool=solo`.

## ✅ Comando Correto para Windows

```powershell
# No diretório back-n1
python -m celery -A app.infra.celery_app worker --pool=solo --loglevel=info
```

## 🔍 Verificar se Está Funcionando

Após iniciar o worker, você deve ver:

```
[tasks]
  . notifications.notify_comment_like
  . notifications.notify_comment_reply
  . notifications.notify_post_comment
  . notifications.notify_post_like
  . notifications.remove_comment_like_notification
  . notifications.remove_post_like_notification

[INFO] Connected to redis://localhost:6379/0
[INFO] celery@Julia ready.
```

## 📝 Quando Você Curtir/Comentar

**No terminal do Uvicorn**, você verá:
```
✅ Task enviada para Celery: notify_post_like - Task ID: xxx-xxx-xxx
```

**No terminal do Celery**, você DEVE ver:
```
[INFO] Task notifications.notify_post_like[xxx-xxx-xxx] received
[INFO] 🔄 Task recebida: notify_post_like - news_id=X, liker_id=Y
[INFO] 📝 Chamando NotificationService.notify_post_like...
[INFO] ✅ Notificação criada com sucesso
```

## 🐧 Para Linux/Produção

No Linux (sua VM), você pode usar o pool padrão:

```bash
python -m celery -A app.infra.celery_app worker --loglevel=info --concurrency=4
```

Ou com Gunicorn + Celery em produção, use systemd (veja `CELERY_SETUP.md`).

## ❌ Se Não Ver Logs de Tasks

1. **Verifique se Redis está rodando:**
   ```powershell
   redis-cli ping
   # Deve retornar: PONG
   ```

2. **Verifique se o worker está conectado ao mesmo Redis:**
   - Mesmo host/porta
   - Mesmo database (padrão: 0)

3. **Reinicie ambos (Uvicorn e Celery):**
   - Pare ambos (Ctrl+C)
   - Inicie novamente

4. **Teste enviando uma task manualmente:**
   ```python
   python
   >>> from app.domain.users.tasks.notification_tasks import notify_post_like_task
   >>> result = notify_post_like_task.delay(10, 1)
   >>> print(result.id)
   ```







