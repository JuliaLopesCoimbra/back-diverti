from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

NOTIFICATION_DATABASE_URL = settings.NOTIFICATIONS_DATABASE_URL

# Configuração de pool otimizada para alta concorrência
# Ajustado para max_connections=400 do PostgreSQL (distribuído entre 6 engines)
# db_notifications: 20 base + 10 overflow = 30 conexões máximas (processado em background)
notification_engine = create_engine(
    NOTIFICATION_DATABASE_URL,
    pool_size=20,              # Número de conexões mantidas no pool (aumentado de 12)
    max_overflow=10,           # Máximo de conexões adicionais além do pool_size (aumentado de 8)
    pool_timeout=30,           # Tempo de espera (segundos) para obter conexão
    pool_recycle=3600,         # Reciclar conexões após 1 hora (evitar timeouts)
    pool_pre_ping=True,        # Verificar conexões antes de usar
    future=True,
    echo=False,                 # Desabilitar logs SQL em produção
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=notification_engine)

NotificationBase = declarative_base()

def get_notification_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

