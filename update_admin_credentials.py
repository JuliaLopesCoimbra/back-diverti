#!/usr/bin/env python3
"""
Script seguro para atualizar as credenciais do admin master.
Este script deve ser executado apenas por administradores autorizados.

Uso:
    python update_admin_credentials.py

O script solicitará:
    - Novo email do admin master
    - Nova senha (com validação de força)
    - Confirmação da senha
"""

import sys
import getpass
import re
from typing import Tuple, List
from sqlalchemy.orm import Session
from app.config.auth_db import SessionLocal
from app.domain.auth.models.user_model import User
from app.core.security.hashing import Hash


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """
    Valida se a senha atende aos requisitos de segurança.
    Retorna (é_válida, lista_de_erros)
    """
    errors = []
    
    if len(password) < 12:
        errors.append("A senha deve ter no mínimo 12 caracteres (recomendado para admin master).")
    
    if len(password) < 8:
        errors.append("A senha deve ter no mínimo 8 caracteres.")
    
    if not re.search(r'[A-Z]', password):
        errors.append("A senha deve conter pelo menos uma letra maiúscula.")
    
    if not re.search(r'[a-z]', password):
        errors.append("A senha deve conter pelo menos uma letra minúscula.")
    
    if not re.search(r'\d', password):
        errors.append("A senha deve conter pelo menos um número.")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append("A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>/?).")
    
    # Validações adicionais para senha extremamente segura
    if len(password) < 16:
        errors.append("⚠️  AVISO: Para admin master, recomenda-se senha com pelo menos 16 caracteres.")
    
    # Verificar se tem pelo menos 3 tipos diferentes de caracteres
    types_count = 0
    if re.search(r'[A-Z]', password):
        types_count += 1
    if re.search(r'[a-z]', password):
        types_count += 1
    if re.search(r'\d', password):
        types_count += 1
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        types_count += 1
    
    if types_count < 3:
        errors.append("A senha deve conter pelo menos 3 tipos diferentes de caracteres (maiúsculas, minúsculas, números, especiais).")
    
    return len(errors) == 0, errors


def validate_email(email: str) -> Tuple[bool, str]:
    """Valida formato de email básico"""
    if not email or not email.strip():
        return False, "Email não pode estar vazio."
    
    email = email.strip().lower()
    
    # Validação básica de formato
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido."
    
    # Não permitir emails genéricos/inseguros
    insecure_domains = ['admin@admin.com', 'admin@admin.com.br', 'test@test.com']
    if email in insecure_domains:
        return False, "Este email é muito genérico e inseguro. Use um email profissional único."
    
    return True, email


def get_admin_master(db: Session) -> User:
    """Busca o admin master no banco de dados"""
    admin = db.query(User).filter(User.role == "admin_master").first()
    
    if not admin:
        raise Exception("❌ Admin master não encontrado no banco de dados.")
    
    return admin


def update_admin_credentials():
    """Função principal para atualizar credenciais do admin master"""
    print("=" * 70)
    print("🔐 ATUALIZAÇÃO DE CREDENCIAIS DO ADMIN MASTER")
    print("=" * 70)
    print()
    print("⚠️  ATENÇÃO: Este script irá alterar as credenciais do admin master.")
    print("    Certifique-se de que você tem autorização para fazer isso.")
    print()
    
    # Confirmar execução
    confirm = input("Deseja continuar? (digite 'SIM' para confirmar): ")
    if confirm != "SIM":
        print("❌ Operação cancelada.")
        return
    
    db: Session = None
    try:
        db = SessionLocal()
        
        # Buscar admin master
        print("\n📋 Buscando admin master no banco de dados...")
        admin = get_admin_master(db)
        print(f"✅ Admin master encontrado: {admin.email} (ID: {admin.id})")
        print()
        
        # Solicitar novo email
        print("=" * 70)
        print("📧 NOVO EMAIL")
        print("=" * 70)
        while True:
            new_email = input("Digite o novo email do admin master: ").strip()
            is_valid, result = validate_email(new_email)
            
            if is_valid:
                # Verificar se o email já está em uso por outro usuário
                existing_user = db.query(User).filter(
                    User.email == result,
                    User.id != admin.id
                ).first()
                
                if existing_user:
                    print(f"❌ Este email já está em uso por outro usuário (ID: {existing_user.id}).")
                    continue
                
                new_email = result
                break
            else:
                print(f"❌ {result}")
        
        # Solicitar nova senha
        print()
        print("=" * 70)
        print("🔑 NOVA SENHA")
        print("=" * 70)
        print("Requisitos de senha:")
        print("  • Mínimo 8 caracteres (recomendado 16+ para admin master)")
        print("  • Pelo menos 1 letra maiúscula")
        print("  • Pelo menos 1 letra minúscula")
        print("  • Pelo menos 1 número")
        print("  • Pelo menos 1 caractere especial")
        print("  • Pelo menos 3 tipos diferentes de caracteres")
        print()
        
        while True:
            new_password = getpass.getpass("Digite a nova senha: ")
            
            if not new_password:
                print("❌ A senha não pode estar vazia.")
                continue
            
            is_valid, errors = validate_password_strength(new_password)
            
            if is_valid:
                # Confirmar senha
                confirm_password = getpass.getpass("Confirme a nova senha: ")
                
                if new_password != confirm_password:
                    print("❌ As senhas não coincidem. Tente novamente.")
                    continue
                
                break
            else:
                print("\n❌ A senha não atende aos requisitos:")
                for error in errors:
                    print(f"   • {error}")
                print()
        
        # Confirmar alteração
        print()
        print("=" * 70)
        print("⚠️  CONFIRMAÇÃO FINAL")
        print("=" * 70)
        print(f"Email atual: {admin.email}")
        print(f"Email novo:  {new_email}")
        print("Senha: [OCULTA]")
        print()
        
        final_confirm = input("Confirma a alteração? (digite 'CONFIRMAR' para prosseguir): ")
        if final_confirm != "CONFIRMAR":
            print("❌ Operação cancelada.")
            return
        
        # Atualizar credenciais
        print("\n🔄 Atualizando credenciais...")
        admin.email = new_email
        admin.password_hash = Hash.hash_password(new_password)
        
        db.commit()
        db.refresh(admin)
        
        print()
        print("=" * 70)
        print("✅ CREDENCIAIS ATUALIZADAS COM SUCESSO!")
        print("=" * 70)
        print(f"Email: {admin.email}")
        print("Senha: [ATUALIZADA]")
        print()
        print("⚠️  IMPORTANTE:")
        print("   1. Guarde essas credenciais em local seguro")
        print("   2. Não compartilhe essas credenciais")
        print("   3. Considere usar um gerenciador de senhas")
        print("   4. Faça logout de todas as sessões antigas se necessário")
        print()
        
    except Exception as e:
        if db:
            db.rollback()
        print(f"\n❌ Erro ao atualizar credenciais: {str(e)}")
        sys.exit(1)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    try:
        update_admin_credentials()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        sys.exit(1)

