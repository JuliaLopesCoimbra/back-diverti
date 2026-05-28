from sqlalchemy.orm import Session
from app.domain.auth.models.user_model import User
from app.core.security.hashing import Hash
import os

def seed_admin(db: Session):
    admin_exists = db.query(User).filter(User.role.in_(["admin", "admin_master"])).first()
    
    if admin_exists:
        return
    
    # Verificar se está em ambiente de produção
    env = os.getenv("ENV", "development").lower()
    
    if env == "production":
        # Em produção, não criar admin com credenciais padrão
        print("⚠️  ATENÇÃO: Ambiente de produção detectado.")
        print("   Não foi criado admin master com credenciais padrão por segurança.")
        print("   Use o script 'update_admin_credentials.py' para criar/atualizar o admin master.")
        return
    
    # Apenas em desenvolvimento: criar admin com credenciais padrão
    admin = User(
        name="Admin",
        email="admin@admin.com",
        password_hash=Hash.hash_password("admin123"),
        role="admin_master",  
        is_email_verified=True,
        status="active"
    )

    db.add(admin)
    db.commit()
    print("⚠️  ATENÇÃO DE SEGURANÇA:")
    print("✅ Admin inicial criado: admin@admin.com | senha: admin123")
    print("   ⚠️  Estas credenciais são EXTREMAMENTE INSECURAS!")
    print("   ⚠️  ALTERE IMEDIATAMENTE usando: python update_admin_credentials.py")
    print("   ⚠️  NUNCA use estas credenciais em produção!")
