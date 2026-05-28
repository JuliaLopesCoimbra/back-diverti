from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

# Configuração de pool otimizada para alta concorrência
# Ajustado para max_connections=400 do PostgreSQL (distribuído entre 6 engines)
# admin_engine: 30 base + 15 overflow = 45 conexões máximas
# auth_engine: 30 base + 15 overflow = 45 conexões máximas
POOL_CONFIG = {
    'pool_size': 30,            # Aumentado de 18 para 30
    'max_overflow': 15,        # Aumentado de 12 para 15
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'future': True,
    'echo': False,
    'connect_args': {"sslmode": "require"}
}

admin_engine = create_engine(
    settings.ADMIN_DATABASE_URL,
    **POOL_CONFIG
)
# Banco de dados de autenticação (db_auth)
auth_engine = create_engine(
    settings.AUTH_DATABASE_URL,  # URL do banco de autenticação
    **POOL_CONFIG
)

AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

AdminBase = declarative_base()

def get_admin_db():
    db = AdminSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Função para obter uma sessão para o db_auth
def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()