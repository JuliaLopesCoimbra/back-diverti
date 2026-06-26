"""
Cria uma conta de operador (cozinha/garcom) direto no banco.
  cd back
  python seed_operador.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Importa apenas o necessário, sem disparar o boot do Redis
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

EMAIL    = "operacao@diverti.com.br"
PASSWORD = "Diverti@2026"
NAME     = "Operacao Diverti"

# Hash da senha usando o mesmo esquema do app (argon2)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
pw_hash = pwd_context.hash(PASSWORD)

# Conecta direto no banco de auth (mesma URL do auth_db.py)
DATABASE_URL = os.getenv("AUTH_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Tenta ler do .env manualmente
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("AUTH_DATABASE_URL="):
                DATABASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
            if line.startswith("DATABASE_URL=") and not DATABASE_URL:
                DATABASE_URL = line.split("=", 1)[1].strip().strip('"').strip("'")

if not DATABASE_URL:
    print("ERRO: AUTH_DATABASE_URL ou DATABASE_URL nao encontrada no .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    existing = conn.execute(text("SELECT id FROM users WHERE email = :e"), {"e": EMAIL}).fetchone()
    if existing:
        print(f"INFO  Operador ja existe (id={existing[0]})")
        print(f"  Email: {EMAIL}")
        print(f"  Senha: {PASSWORD}")
        sys.exit(0)

    row = conn.execute(text("""
        INSERT INTO users (name, email, password_hash, role, is_email_verified, age_verified, status)
        VALUES (:name, :email, :pw, 'operador', true, true, 'active')
        RETURNING id
    """), {"name": NAME, "email": EMAIL, "pw": pw_hash}).fetchone()

    print(f"OK  Operador criado (id={row[0]})")
    print(f"  Email: {EMAIL}")
    print(f"  Senha: {PASSWORD}")
    print(f"  Acesso: http://localhost:3000/pages/operation")
