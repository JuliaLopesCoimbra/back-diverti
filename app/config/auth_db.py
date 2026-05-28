from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

# Criar engine do SQLAlchemy com configuração de pool otimizada para alta concorrência
# Ajustado para max_connections=400 do PostgreSQL (distribuído entre 6 engines)
# db_auth: 50 base + 30 overflow = 80 conexões máximas
engine = create_engine(
    settings.AUTH_DATABASE_URL.strip(),
    pool_size=50,              # Número de conexões mantidas no pool (aumentado de 25)
    max_overflow=30,           # Máximo de conexões adicionais além do pool_size (aumentado de 20)
    pool_timeout=30,            # Tempo de espera (segundos) para obter conexão
    pool_recycle=3600,          # Reciclar conexões após 1 hora (evitar timeouts)
    pool_pre_ping=True,         # Verificar conexões antes de usar
    future=True,
    echo=False,                 # Desabilitar logs SQL em produção
    connect_args={"sslmode": "require"}
)

# Criar SessionLocal (sessão por request)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
