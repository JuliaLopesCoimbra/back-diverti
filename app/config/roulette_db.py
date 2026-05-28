from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

ROULETTE_DATABASE_URL = settings.ROULETTE_DATABASE_URL

# Configuração de pool otimizada para alta concorrência
# Ajustado para max_connections=400 do PostgreSQL (distribuído entre 6 engines)
# db_roulette: 35 base + 20 overflow = 55 conexões máximas (picos altos durante spins)
roulette_engine = create_engine(
    ROULETTE_DATABASE_URL,
    pool_size=35,              # Número de conexões mantidas no pool (aumentado de 18)
    max_overflow=20,           # Máximo de conexões adicionais além do pool_size (aumentado de 12)
    pool_timeout=30,           # Tempo de espera (segundos) para obter conexão
    pool_recycle=3600,         # Reciclar conexões após 1 hora (evitar timeouts)
    pool_pre_ping=True,        # Verificar conexões antes de usar
    future=True,
    echo=False,                 # Desabilitar logs SQL em produção
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=roulette_engine)

RouletteBase = declarative_base()

def get_roulette_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
