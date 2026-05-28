# Configuração do Redis para Cache

## Problema Identificado

Os logs mostram `redis_connected=False`, o que significa que o Redis não está rodando ou não está acessível.

## Como Resolver

### 1. Verificar se o Redis está instalado

**Windows:**
```powershell
# Verificar se Redis está instalado
redis-cli --version
```

**Linux/Mac:**
```bash
redis-cli --version
```

### 2. Iniciar o Redis

**Windows (se instalado via WSL ou Docker):**
```powershell
# Via Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Ou via WSL
wsl redis-server
```

**Linux:**
```bash
sudo systemctl start redis
# ou
redis-server
```

**Mac (via Homebrew):**
```bash
brew services start redis
```

### 3. Verificar se está rodando

```bash
redis-cli ping
# Deve retornar: PONG
```

### 4. Verificar configurações no .env

Certifique-se de que o arquivo `.env` tem as configurações corretas:

```env
# Opção 1: Usar variáveis individuais
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Opção 2: Usar URL completa (sobrescreve as variáveis acima)
# REDIS_URL=redis://localhost:6379/0
```

### 5. Reiniciar o servidor FastAPI

Após iniciar o Redis, reinicie o servidor:

```bash
# Pare o servidor (Ctrl+C) e inicie novamente
uvicorn app.main:app --reload
```

### 6. Verificar se conectou

Ao iniciar o servidor, você deve ver:
```
✅ Redis conectado com sucesso
```

Se não aparecer essa mensagem, verifique os logs de erro.

## Alternativa: Instalar Redis no Windows

### Opção 1: Docker (Recomendado)
```powershell
docker pull redis
docker run -d -p 6379:6379 --name redis redis:latest
```

### Opção 2: WSL2
```powershell
wsl --install
# Depois no WSL:
sudo apt update
sudo apt install redis-server
redis-server
```

### Opção 3: Memurai (Redis para Windows)
Baixe em: https://www.memurai.com/

## Impacto Sem Redis

Sem Redis conectado:
- ❌ Cache não funciona
- ❌ Cada requisição leva ~1900ms
- ❌ Performance degradada

Com Redis conectado:
- ✅ Cache funciona
- ✅ Segunda requisição: ~5-10ms (cache hit)
- ✅ Performance muito melhor

## Teste Rápido

Após configurar, teste:

1. Primeira requisição: Deve ver `Cache miss` mas salvar no cache
2. Segunda requisição: Deve ver `CACHE HIT` e ser muito mais rápida

