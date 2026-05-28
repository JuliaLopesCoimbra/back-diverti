# 🚀 Instruções: Sistema de Views com Batch Processing

## ✅ O que foi implementado

1. ✅ Modelo `AdView` criado
2. ✅ Schemas para views adicionados
3. ✅ Batch processing implementado (processa 50 views a cada 5s)
4. ✅ Rotas configuradas com rate limiting
5. ✅ Worker thread automático (inicia sozinho)

## 📝 Passo 1: Criar a Tabela no Banco de Dados

Execute o SQL no banco **admin_db**:

### Opção A: Via arquivo SQL
```bash
psql -h SEU_HOST -U SEU_USUARIO -d SEU_BANCO_ADMIN -f migrations/create_ad_views_table.sql
```

### Opção B: Copiar e colar no cliente PostgreSQL
```sql
-- Copie todo o conteúdo de: migrations/create_ad_views_table.sql
-- E cole no seu cliente PostgreSQL (pgAdmin, DBeaver, etc)
```

### Opção C: SQL direto (se preferir)
```sql
CREATE TABLE IF NOT EXISTS ad_views (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_id INTEGER NOT NULL REFERENCES events(id),
    ad_identifier VARCHAR(255) NOT NULL,
    ad_url TEXT,
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_views_user_id ON ad_views(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ad_views_event_id ON ad_views(event_id);
CREATE INDEX IF NOT EXISTS idx_ad_views_viewed_at ON ad_views(viewed_at);
CREATE INDEX IF NOT EXISTS idx_ad_views_ad_identifier ON ad_views(ad_identifier);
CREATE INDEX IF NOT EXISTS idx_ad_views_event_ad ON ad_views(event_id, ad_identifier, viewed_at);
```

**Nota:** O índice composto `idx_ad_views_event_ad` já otimiza queries por hora de forma eficiente, então não precisamos de um índice separado com EXTRACT.

## 🔄 Passo 2: Reiniciar o Servidor

O sistema **já está configurado**! Apenas reinicie o servidor:

```bash
# Se estiver usando uvicorn diretamente
uvicorn app.main:app --reload

# Se estiver usando docker
docker-compose restart backend

# Ou reinicie o serviço como preferir
```

## ✅ Passo 3: Verificar se Está Funcionando

### 3.1 Verificar logs do servidor

Quando a primeira view for registrada, você verá:
```
🚀 Batch worker thread iniciado para processamento de views
```

Quando um batch for processado:
```
✅ Processadas 50 views em batch
```

### 3.2 Testar a API

```bash
# Registrar uma view (retorna 202 Accepted)
curl -X POST http://localhost:8000/ads/views \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": 1,
    "ad_identifier": "1",
    "ad_url": "/ads/1.png"
  }'

# Ver estatísticas de views
curl http://localhost:8000/ads/views/stats?event_id=1
```

## 🎯 Como Funciona o Batch Processing

1. **Frontend** envia view → API retorna `202 Accepted` **imediatamente**
2. **Backend** adiciona view à fila em memória (thread-safe)
3. **Worker thread** processa automaticamente:
   - A cada **5 segundos** OU quando atinge **50 views**
   - Faz **bulk insert** no banco (muito eficiente)
   - Processa até 50 views por vez

## ⚙️ Configurações (Opcional)

Se quiser ajustar, edite `ad_click_controller.py`:

```python
_batch_size = 50        # Quantas views processar por vez
_batch_timeout = 5      # Segundos entre processamentos
```

**Recomendações:**
- **5000+ usuários**: Mantenha como está (50 views, 5s)
- **Menos usuários**: Pode reduzir para `batch_size=20` e `timeout=10`

## 📊 Endpoints Disponíveis

### Registrar View (Assíncrono)
```
POST /ads/views
Body: {
  "event_id": 1,
  "ad_identifier": "1",
  "ad_url": "/ads/1.png"
}
Response: 202 Accepted
```

### Registrar Clique (Síncrono)
```
POST /ads/clicks
Body: {
  "event_id": 1,
  "ad_identifier": "1",
  "ad_url": "/ads/1.png",
  "redirect_url": "https://..."
}
Response: 201 Created
```

### Estatísticas de Views
```
GET /ads/views/stats?event_id=1&start_date=2024-01-01&end_date=2024-12-31
```

### Estatísticas de Cliques
```
GET /ads/stats?event_id=1&start_date=2024-01-01&end_date=2024-12-31
```

## 🔒 Rate Limiting

- **Views**: 10 views/min por IP
- **Clicks**: 30 clicks/min por IP

## 🐛 Troubleshooting

### Views não estão sendo processadas?

1. Verifique os logs do servidor
2. Confirme que a tabela `ad_views` existe:
   ```sql
   SELECT * FROM ad_views LIMIT 1;
   ```
3. Verifique se há erros no worker thread nos logs

### Performance lenta?

1. Aumente `_batch_size` para 100
2. Reduza `_batch_timeout` para 3 segundos
3. Verifique índices do banco:
   ```sql
   \d ad_views
   ```

## 📈 Performance Esperada

Com **5000 usuários simultâneos**:
- ✅ **Views/min**: ~500-1000 views/min
- ✅ **Processamento**: 50 views a cada 5s = **600 views/min**
- ✅ **Latência**: < 5 segundos (tempo de batch)
- ✅ **Carga no banco**: Mínima (bulk inserts)

## ✨ Pronto!

O sistema está configurado e pronto para uso. O batch processing inicia automaticamente quando a primeira view é registrada.

