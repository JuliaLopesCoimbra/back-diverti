# app/config/interaction_db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

INTERACTION_DATABASE_URL = settings.INTERACTION_DATABASE_URL

# Configuração de pool otimizada para alta concorrência
# Ajustado para max_connections=400 do PostgreSQL (distribuído entre 6 engines)
# db_interaction: 45 base + 25 overflow = 70 conexões máximas (muito usado para likes/comments)
interaction_engine = create_engine(
    INTERACTION_DATABASE_URL,
    pool_size=45,              # Número de conexões mantidas no pool (aumentado de 22)
    max_overflow=25,           # Máximo de conexões adicionais além do pool_size (aumentado de 18)
    pool_timeout=30,           # Tempo de espera (segundos) para obter conexão
    pool_recycle=3600,         # Reciclar conexões após 1 hora (evitar timeouts)
    pool_pre_ping=True,        # Verificar conexões antes de usar
    future=True,
    echo=False,               # Desabilitar logs SQL em produção
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=interaction_engine)

InteractionBase = declarative_base()

def get_interaction_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
