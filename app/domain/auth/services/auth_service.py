from app.core.security.hashing import Hash
from app.core.security.jwt import JWTHandler
from app.core.security.password_validator import validate_password
from datetime import datetime, timedelta, timezone, date
from app.domain.auth.repositories.auth_repository import AuthRepository
from fastapi import HTTPException, status
from app.core.security.auth_dependency import invalidate_user_cache

from app.domain.auth.repositories.email_repository import EmailVerificationRepository
from app.domain.auth.services.email_verification_service import EmailVerificationService

class AuthService:

    @staticmethod
    def register(db, data, user_agent: str = None, ip: str = None, current_user=None):
        # Validação de senha (também validada pelo Pydantic, mas garantia extra)
        validate_password(data.password)

        # Validar idade
        today = date.today()
        age = today.year - data.birth_date.year - ((today.month, today.day) < (data.birth_date.month, data.birth_date.day))
        if age < 18:
            raise HTTPException(
                status_code=400,
                detail="Você deve ter pelo menos 18 anos para se cadastrar."
            )

        # Verificar se CPF já existe PRIMEIRO (antes de verificar email)
        # Isso permite corrigir email quando CPF existe mas email não foi verificado
        from app.domain.auth.models.user_model import User
        existing_cpf = db.query(User).filter(User.cpf == data.cpf).first()
        if existing_cpf:
            # Se o email não foi verificado, retornar erro especial para o frontend tratar
            if not existing_cpf.is_email_verified:
                raise HTTPException(
                    status_code=428,  # 428 Precondition Required - indica que precisa de ação do usuário
                    detail="CPF já cadastrado. O email cadastrado ainda não foi verificado. Por favor, informe o email correto para receber o código de verificação."
                )
            else:
                raise HTTPException(status_code=400, detail="CPF já cadastrado.")

        # Verificar se email já existe (só depois de verificar CPF)
        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            if not existing.password_hash:
                raise HTTPException(
                    status_code=400,
                    detail="Esse email já possui conta via Google. Entre com Google ou Facebook."
                )
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Registrar data, IP e user agent do aceite de termos
        now = datetime.now(timezone.utc)
        password_hash = Hash.hash_password(data.password)
        user = AuthRepository.create_user(
            db,
            data.name,
            data.email,
            password_hash,
            role="user",
            birth_date=data.birth_date,
            age_verified=True,  # No registro normal, já validamos
            cpf=data.cpf,
            gender=data.gender,
            lgpd_accepted=data.lgpd_accepted,
            age_terms_accepted=data.age_terms_accepted,
            marketing_email_accepted=data.marketing_email_accepted,
            lgpd_accepted_at=now if data.lgpd_accepted else None,
            lgpd_accepted_ip=ip if data.lgpd_accepted else None,
            lgpd_accepted_user_agent=user_agent if data.lgpd_accepted else None,
            age_terms_accepted_at=now if data.age_terms_accepted else None,
            age_terms_accepted_ip=ip if data.age_terms_accepted else None,
            age_terms_accepted_user_agent=user_agent if data.age_terms_accepted else None
        )

        EmailVerificationService.send_verification_email(db, user)

        return user

    @staticmethod
    def login(db, data, user_agent, ip):
        user = AuthRepository.get_user_by_email(db, data.email)
        if not user:
            raise HTTPException(status_code=404, detail="Email não encontrado. Cadastre-se para criar uma conta.")
        if not user.password_hash:
            raise HTTPException(
                status_code=400,
                detail="Essa conta utiliza login social. Entre com Google ou Facebook."
            )
        if not user.is_email_verified:
            raise HTTPException(
                status_code=403,
                detail="Confirme seu e-mail antes de acessar o sistema."
            )

        # Verificar se usuário está ativo
        if user.status != "active":
            raise HTTPException(
                status_code=403,
                detail="Sua conta foi desativada. Entre em contato com o administrador."
            )

        # Verificar senha primeiro
        if not Hash.verify(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

        # Verificações de perfil apenas para usuários comuns
        if user.role == "user":
            # Verificar se precisa confirmar idade - se sim, retornar token temporário
            if not user.age_verified:
                # Criar token temporário para verificação de idade
                temp_token = JWTHandler.create_access_token({
                    "sub": str(user.id),
                    "role": user.role,
                    "temp": True
                }, expires_minutes=10)

                # Retornar erro especial com token temporário no detail (formato JSON string)
                import json
                error_detail = {
                    "message": "Você precisa confirmar que é maior de idade antes de acessar o sistema.",
                    "requires_age_verification": True,
                    "temp_token": temp_token
                }
                raise HTTPException(
                    status_code=403,
                    detail=json.dumps(error_detail)
                )

            # Verificar se precisa completar perfil (CPF, sexo e termos)
            if not user.cpf or not user.gender or not user.lgpd_accepted or not user.age_terms_accepted:
                # Criar token temporário para completar perfil
                temp_token = JWTHandler.create_access_token({
                    "sub": str(user.id),
                    "role": user.role,
                    "temp": True,
                    "requires_profile_completion": True
                }, expires_minutes=30)

                # Retornar erro especial com token temporário no detail (formato JSON string)
                import json
                error_detail = {
                    "message": "Você precisa completar seu perfil antes de acessar o sistema.",
                    "requires_profile_completion": True,
                    "temp_token": temp_token
                }
                raise HTTPException(
                    status_code=403,
                    detail=json.dumps(error_detail)
                )

        token_payload = {
            "sub": str(user.id),
            "role": user.role,
            "name": user.name,
        }
        if user.role == "operador" and getattr(user, "restaurant_id", None):
            token_payload["restaurant_id"] = user.restaurant_id
        access = JWTHandler.create_access_token(token_payload)

        # Se remember_me estiver marcado, refresh token expira em 90 dias
        # Caso contrário, expira em 7 dias (sessão)
        remember_me = getattr(data, 'remember_me', False)
        refresh_expires_days = 90 if remember_me else 7

        refresh = JWTHandler.create_refresh_token({
            "sub": str(user.id)
        }, expires_days=refresh_expires_days)

        expires = datetime.now(timezone.utc) + timedelta(days=refresh_expires_days)
        AuthRepository.save_refresh_token(db, user.id, refresh, user_agent, ip, expires)

        # Atualizar last_login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # Limpeza leve de tokens expirados (não bloqueia o login)
        try:
            AuthRepository.cleanup_expired_tokens_lazy(db)
        except Exception:
            # Se falhar a limpeza, não afeta o login
            pass

        return access, refresh

    @staticmethod
    def refresh(db, refresh_token: str, user_agent: str, ip: str):
        token_model = AuthRepository.get_refresh_token(db, refresh_token)

        if not token_model:
            raise HTTPException(
                status_code=401,
                detail="Refresh token inválido ou revogado."
            )

        try:
            payload = JWTHandler.decode_token(refresh_token, refresh=True)
        except:
            raise HTTPException(
                status_code=401,
                detail="Refresh token expirado."
            )

        user_id = int(payload["sub"])

        # BUSCAR USUÁRIO PARA PEGAR O ROLE
        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Usuário não encontrado.")

        # Verificar se usuário está ativo
        if user.status != "active":
            # Invalidar todos os tokens do usuário
            AuthRepository.revoke_all_user_tokens(db, user_id)
            raise HTTPException(
                status_code=403,
                detail="Sua conta foi desativada. Entre em contato com o administrador."
            )

        # Verificar se precisa completar perfil (CPF, sexo e termos)
        # Nota: Não bloqueamos o refresh, mas o usuário será bloqueado no próximo login
        # Isso permite que tokens existentes continuem funcionando por um período de transição

        # Revogar o refresh token antigo
        AuthRepository.revoke_token(db, token_model)

        # NOVO ACCESS TOKEN COM ROLE
        access = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role,
            "name": user.name
        })

        # Criar novo refresh token
        new_refresh = JWTHandler.create_refresh_token({
            "sub": str(user.id)
        })

        expires = datetime.now(timezone.utc) + timedelta(days=30)

        AuthRepository.save_refresh_token(
            db,
            user_id=user.id,
            token=new_refresh,
            agent=user_agent,
            ip=ip,
            expires_at=expires
        )

        # Limpeza leve de tokens expirados (não bloqueia o refresh)
        try:
            AuthRepository.cleanup_expired_tokens_lazy(db)
        except Exception:
            # Se falhar a limpeza, não afeta o refresh
            pass

        return access, new_refresh

    @staticmethod
    def logout(db, refresh_token: str):
        token_model = AuthRepository.get_refresh_token(db, refresh_token)

        if not token_model:
            return {"message": "Token já inválido."}

        AuthRepository.revoke_token(db, token_model)

        return {"message": "Logout realizado com sucesso."}

    @staticmethod
    def create_admin_by_admin(db, data, admin):
        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Criar usuário sem senha - será definida no primeiro acesso
        user = AuthRepository.create_user(
            db=db,
            name=data.name,
            email=data.email,
            password_hash=None,
            role="admin"
        )

        # força confirmação / primeiro acesso
        user.is_email_verified = False
        db.commit()

        EmailVerificationService.send_first_access_email(db, user)

        return {"message": "Admin criado. Email de primeiro acesso enviado."}

    @staticmethod
    def first_access(db, token: str, new_password: str):
        # Validação de senha
        validate_password(new_password)

        token_model = EmailVerificationRepository.get_token(db, token)
        if not token_model:
            raise HTTPException(status_code=400, detail="Token inválido ou expirado.")

        user = token_model.user

        user.password_hash = Hash.hash_password(new_password)
        user.is_email_verified = True

        EmailVerificationRepository.mark_used(db, token_model)
        db.commit()

        return {
            "message": "Senha definida com sucesso. Você já pode acessar o sistema."
        }

    @staticmethod
    def invite_admin(db, data, admin):
        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Criar usuário sem senha - será definida no primeiro acesso
        user = AuthRepository.create_user(
            db=db,
            name=data.name,
            email=data.email,
            password_hash=None,
            role="admin"
        )

        # bloqueia login até primeiro acesso
        user.is_email_verified = False
        db.commit()

        EmailVerificationService.send_first_access_email(db, user)

        return {
            "message": "Admin convidado com sucesso. Email de primeiro acesso enviado."
        }

    @staticmethod
    def resend_admin_invite(db, email: str):
        user = AuthRepository.get_user_by_email(db, email)

        # resposta genérica (não vaza info)
        if not user:
            return {
                "message": "Se o admin existir, o convite será reenviado."
            }

        if user.role not in ["admin", "admin_master"]:
            return {
                "message": "Este usuário não é administrador."
            }

        if user.is_email_verified:
            return {
                "message": "Este administrador já ativou a conta."
            }

        EmailVerificationService.send_first_access_email(db, user)

        return {
            "message": "Convite de primeiro acesso reenviado com sucesso."
        }

    @staticmethod
    def invite_admin_user(db, data, admin_master):
        """Apenas admin_master pode convidar admin"""
        if admin_master.role != "admin_master":
            raise HTTPException(status_code=403, detail="Apenas admin master pode convidar admins.")

        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Criar usuário sem senha - será definida no primeiro acesso
        user = AuthRepository.create_user(
            db=db,
            name=data.name,
            email=data.email,
            password_hash=None,
            role="admin",
            invited_by_id=admin_master.id
        )

        user.is_email_verified = False
        db.commit()

        EmailVerificationService.send_first_access_email(db, user)

        return {"message": "Admin convidado com sucesso. Email de primeiro acesso enviado."}

    @staticmethod
    def invite_patrocinador(db, data, inviter):
        """Admin_master e admin podem convidar patrocinador"""
        if inviter.role not in ["admin_master", "admin"]:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem convidar patrocinadores.")

        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        # Criar usuário sem senha - será definida no primeiro acesso
        user = AuthRepository.create_user(
            db=db,
            name=data.name,
            email=data.email,
            password_hash=None,
            role="patrocinador",
            invited_by_id=inviter.id
        )

        user.is_email_verified = False
        db.commit()

        EmailVerificationService.send_first_access_email(db, user)

        return {"message": "Patrocinador convidado com sucesso. Email de primeiro acesso enviado."}

    @staticmethod
    def revoke_patrocinador_access(db, patrocinador_id: int, revoker):
        """Admin pode revogar acesso de patrocinadores que ele convidou"""
        patrocinador = AuthRepository.get_user_by_id(db, patrocinador_id)
        if not patrocinador:
            raise HTTPException(status_code=404, detail="Patrocinador não encontrado.")

        if patrocinador.role != "patrocinador":
            raise HTTPException(status_code=400, detail="Usuário não é um patrocinador.")

        # Verificar permissão
        if revoker.role == "admin_master":
            # Admin master pode revogar qualquer patrocinador
            pass
        elif revoker.role == "admin":
            # Admin só pode revogar patrocinadores que ele convidou
            if patrocinador.invited_by_id != revoker.id:
                raise HTTPException(status_code=403, detail="Você só pode revogar acesso de patrocinadores que você convidou.")
        else:
            raise HTTPException(status_code=403, detail="Você não tem permissão para revogar acesso.")

        # Desativar usuário e rastrear quem desativou
        patrocinador.status = "inactive"
        patrocinador.deactivated_by_id = revoker.id
        patrocinador.deactivated_at = datetime.utcnow()
        patrocinador.reactivated_by_id = None
        patrocinador.reactivated_at = None

        # Invalidar todos os refresh tokens do patrocinador
        AuthRepository.revoke_all_user_tokens(db, patrocinador_id)

        db.commit()

        # Invalida cache do usuário
        invalidate_user_cache(patrocinador_id)

        return {"message": "Acesso do patrocinador revogado com sucesso. Todos os tokens foram invalidados."}

    @staticmethod
    def revoke_admin_access(db, admin_id: int, admin_master):
        """Apenas admin_master pode revogar acesso de admin"""
        if admin_master.role != "admin_master":
            raise HTTPException(status_code=403, detail="Apenas admin master pode revogar acesso de admins.")

        admin = AuthRepository.get_user_by_id(db, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado.")

        if admin.role != "admin":
            raise HTTPException(status_code=400, detail="Usuário não é um admin.")

        # Desativar usuário e rastrear quem desativou
        admin.status = "inactive"
        admin.deactivated_by_id = admin_master.id
        admin.deactivated_at = datetime.utcnow()
        admin.reactivated_by_id = None
        admin.reactivated_at = None

        # Invalidar todos os refresh tokens do admin
        AuthRepository.revoke_all_user_tokens(db, admin_id)

        db.commit()

        # Invalida cache do usuário
        invalidate_user_cache(admin_id)

        return {"message": "Acesso do admin revogado com sucesso. Todos os tokens foram invalidados."}

    @staticmethod
    def revoke_user_access(db, user_id: int, revoker):
        """Admin_master e admin podem revogar acesso de users"""
        if revoker.role not in ["admin_master", "admin"]:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem revogar acesso de usuários.")

        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        if user.role != "user":
            raise HTTPException(status_code=400, detail="Usuário não é um user comum.")

        # Desativar usuário e rastrear quem desativou
        user.status = "inactive"
        user.deactivated_by_id = revoker.id
        user.deactivated_at = datetime.utcnow()
        user.reactivated_by_id = None
        user.reactivated_at = None

        # Invalidar todos os refresh tokens do user
        AuthRepository.revoke_all_user_tokens(db, user_id)

        db.commit()

        # Invalida cache do usuário
        invalidate_user_cache(user_id)

        return {"message": "Acesso do usuário revogado com sucesso. Todos os tokens foram invalidados."}

    @staticmethod
    def reactivate_patrocinador_access(db, patrocinador_id: int, reactivator):
        """Admin e master podem reativar acesso de patrocinadores"""
        if reactivator.role not in ["admin_master", "admin"]:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem reativar acesso de patrocinadores.")

        patrocinador = AuthRepository.get_user_by_id(db, patrocinador_id)
        if not patrocinador:
            raise HTTPException(status_code=404, detail="Patrocinador não encontrado.")

        if patrocinador.role != "patrocinador":
            raise HTTPException(status_code=400, detail="Usuário não é um patrocinador.")

        # Verificar permissão para reativar
        if reactivator.role == "admin_master":
            # Admin master pode reativar qualquer patrocinador
            pass
        elif reactivator.role == "admin":
            # Admin só pode reativar patrocinadores que ele convidou ou desativou
            if patrocinador.invited_by_id != reactivator.id and patrocinador.deactivated_by_id != reactivator.id:
                raise HTTPException(status_code=403, detail="Você só pode reativar acesso de patrocinadores que você convidou ou desativou.")

        # Reativar usuário e rastrear quem reativou
        patrocinador.status = "active"
        patrocinador.reactivated_by_id = reactivator.id
        patrocinador.reactivated_at = datetime.utcnow()

        db.commit()

        # Invalida cache para forçar atualização
        invalidate_user_cache(patrocinador_id)

        return {"message": "Acesso do patrocinador reativado com sucesso."}

    @staticmethod
    def reactivate_admin_access(db, admin_id: int, admin_master):
        """Apenas admin_master pode reativar acesso de admin"""
        if admin_master.role != "admin_master":
            raise HTTPException(status_code=403, detail="Apenas admin master pode reativar acesso de admins.")

        admin = AuthRepository.get_user_by_id(db, admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="Admin não encontrado.")

        if admin.role != "admin":
            raise HTTPException(status_code=400, detail="Usuário não é um admin.")

        # Reativar usuário e rastrear quem reativou
        admin.status = "active"
        admin.reactivated_by_id = admin_master.id
        admin.reactivated_at = datetime.utcnow()

        db.commit()

        # Invalida cache para forçar atualização
        invalidate_user_cache(admin_id)

        return {"message": "Acesso do admin reativado com sucesso."}

    @staticmethod
    def reactivate_user_access(db, user_id: int, reactivator):
        """Admin_master e admin podem reativar acesso de users"""
        if reactivator.role not in ["admin_master", "admin"]:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem reativar acesso de usuários.")

        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        if user.role != "user":
            raise HTTPException(status_code=400, detail="Usuário não é um user comum.")

        # Reativar usuário e rastrear quem reativou
        user.status = "active"
        user.reactivated_by_id = reactivator.id
        user.reactivated_at = datetime.utcnow()

        db.commit()

        # Invalida cache para forçar atualização
        invalidate_user_cache(user_id)

        return {"message": "Acesso do usuário reativado com sucesso."}

    @staticmethod
    def list_admins(db, requester, limit: int = 50, offset: int = 0):
        """Lista admins - apenas master pode ver todos"""
        if requester.role != "admin_master":
            raise HTTPException(status_code=403, detail="Apenas admin master pode ver lista de admins.")

        admins = AuthRepository.list_admins(db, limit, offset)
        return admins

    @staticmethod
    def list_patrocinadores(db, requester, limit: int = 50, offset: int = 0):
        """Lista patrocinadores - master vê todos, admin vê apenas os que ele convidou"""
        if requester.role == "admin_master":
            # Master vê todos
            patrocinadores = AuthRepository.list_patrocinadores(db, limit=limit, offset=offset)
        elif requester.role == "admin":
            # Admin vê apenas os que ele convidou
            patrocinadores = AuthRepository.list_patrocinadores(db, invited_by_id=requester.id, limit=limit, offset=offset)
        else:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem ver lista de patrocinadores.")

        return patrocinadores

    @staticmethod
    def list_users(db, requester, limit: int = 50, offset: int = 0):
        """Lista users comuns - master e admin podem ver"""
        if requester.role not in ["admin_master", "admin"]:
            raise HTTPException(status_code=403, detail="Apenas admin master ou admin podem ver lista de usuários.")

        users = AuthRepository.list_users(db, limit, offset)
        return users

    @staticmethod
    def verify_age(db, user_id: int, birth_date: date, confirmed: bool, user_agent: str = None, ip: str = None):
        if not confirmed:
            raise HTTPException(
                status_code=400,
                detail="Você deve confirmar que é maior de idade para continuar."
            )

        # Validar idade
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if age < 18:
            raise HTTPException(
                status_code=400,
                detail="Você deve ter pelo menos 18 anos para usar este serviço."
            )

        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        user.birth_date = birth_date
        user.age_verified = True

        # Registrar data, IP e user agent do aceite de termos de maioridade
        if confirmed:
            now = datetime.now(timezone.utc)
            user.age_terms_accepted = True
            user.age_terms_accepted_at = now
            user.age_terms_accepted_ip = ip
            user.age_terms_accepted_user_agent = user_agent

        db.commit()

        # Verificar se precisa completar perfil (CPF e sexo)
        if not user.cpf or not user.gender:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True,
                "requires_profile_completion": True
            }, expires_minutes=30)

            return {
                "message": "Idade verificada com sucesso.",
                "requires_profile_completion": True,
                "temp_token": temp_token
            }

        return {"message": "Idade verificada com sucesso."}

    @staticmethod
    def cleanup_expired_tokens(db, batch_size: int = 5000):
        """
        Limpeza completa de tokens expirados.
        Remove tokens expirados ou revogados há mais de 7 dias.
        """
        deleted_count = AuthRepository.delete_expired_tokens(db, batch_size)
        return {
            "message": f"Limpeza concluída. {deleted_count} tokens removidos.",
            "deleted_count": deleted_count
        }

    @staticmethod
    def complete_profile(db, user_id: int, data, user_agent: str = None, ip: str = None):
        """Completa o perfil do usuário com CPF, sexo e aceite de termos e retorna tokens"""
        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        # Verificar se já tem CPF
        if user.cpf:
            raise HTTPException(status_code=400, detail="Perfil já completo.")

        # Verificar se CPF já existe
        from app.domain.auth.models.user_model import User
        existing_cpf = db.query(User).filter(User.cpf == data.cpf, User.id != user_id).first()
        if existing_cpf:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")

        # Registrar data, IP e user agent do aceite de termos
        now = datetime.now(timezone.utc)

        # Atualizar dados
        user.cpf = data.cpf
        user.gender = data.gender
        user.lgpd_accepted = data.lgpd_accepted
        user.age_terms_accepted = data.age_terms_accepted
        user.marketing_email_accepted = data.marketing_email_accepted

        # Registrar informações de aceite LGPD (se ainda não foi registrado)
        if data.lgpd_accepted and not user.lgpd_accepted_at:
            user.lgpd_accepted_at = now
            user.lgpd_accepted_ip = ip
            user.lgpd_accepted_user_agent = user_agent

        # Registrar informações de aceite de maioridade (se ainda não foi registrado)
        if data.age_terms_accepted and not user.age_terms_accepted_at:
            user.age_terms_accepted_at = now
            user.age_terms_accepted_ip = ip
            user.age_terms_accepted_user_agent = user_agent

        db.commit()

        # Criar tokens de acesso após completar perfil
        access = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role,
            "name": user.name
        })
        refresh = JWTHandler.create_refresh_token({
            "sub": str(user.id)
        })

        # Salvar refresh token se user_agent e ip foram fornecidos
        if user_agent and ip:
            expires = datetime.now(timezone.utc) + timedelta(days=30)
            AuthRepository.save_refresh_token(db, user.id, refresh, user_agent, ip, expires)

            # Atualizar last_login quando perfil é completado e tokens são gerados
            user.last_login = datetime.now(timezone.utc)
            db.commit()

        return {
            "message": "Perfil completado com sucesso.",
            "access_token": access,
            "refresh_token": refresh
        }

    @staticmethod
    def complete_email(db, user_id: int, data, user_agent: str = None, ip: str = None):
        """Atualiza o email do usuário quando não foi retornado pelo Facebook e envia email de verificação"""
        user = AuthRepository.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        # Verificar se o email já não é temporário
        if user.email and "@facebook.user" not in user.email and "@facebook.temp" not in user.email and "@instagram.user" not in user.email:
            raise HTTPException(status_code=400, detail="Email já foi definido.")

        # Verificar se o email já existe para outro usuário
        existing_user = AuthRepository.get_user_by_email(db, data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="Este email já está em uso.")

        # Atualizar email (NÃO marcar como verificado ainda)
        user.email = data.email
        user.is_email_verified = False  # NÃO marcar como verificado - precisa verificar via email
        db.commit()
        db.refresh(user)

        # Enviar email de verificação
        EmailVerificationService.send_verification_email(db, user)

        # Retornar token temporário para que o usuário possa verificar o email
        # O usuário não pode continuar até verificar o email
        temp_token = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role,
            "temp": True,
            "requires_email_verification": True
        }, expires_minutes=60)  # Token válido por 1 hora para verificar email

        return {
            "message": "Email cadastrado com sucesso! Verifique sua caixa de entrada para confirmar seu email.",
            "requires_email_verification": True,
            "temp_token": temp_token,
            "email": data.email
        }

    @staticmethod
    def update_email_by_cpf(db, cpf: str, new_email: str, user_agent: str = None, ip: str = None):
        """
        Atualiza o email de um usuário que tem CPF cadastrado mas email não verificado.
        Usado quando o usuário digitou email errado no cadastro.
        """
        from app.domain.auth.models.user_model import User

        # Buscar usuário por CPF
        user = db.query(User).filter(User.cpf == cpf).first()
        if not user:
            raise HTTPException(status_code=404, detail="CPF não encontrado.")

        # Verificar se o email já foi verificado
        if user.is_email_verified:
            raise HTTPException(
                status_code=400,
                detail="Este CPF já possui um email verificado. Não é possível atualizar."
            )

        # Verificar se o novo email já está em uso por outro usuário
        existing_email = AuthRepository.get_user_by_email(db, new_email)
        if existing_email and existing_email.id != user.id:
            if not existing_email.password_hash:
                raise HTTPException(
                    status_code=400,
                    detail="Esse email já possui conta via Google. Entre com Google ou Facebook."
                )
            raise HTTPException(status_code=400, detail="Este email já está em uso.")

        # Atualizar email
        user.email = new_email
        user.is_email_verified = False  # Garantir que continua não verificado
        db.commit()
        db.refresh(user)

        # Enviar email de verificação para o novo email
        EmailVerificationService.send_verification_email(db, user)

        return {
            "message": "Email atualizado com sucesso! Verifique sua caixa de entrada para confirmar o novo email."
        }

    @staticmethod
    def create_operador(db, data, creator):
        """Admin ou admin_master podem criar contas de operador (cozinha/garçom)"""
        if creator.role not in ("admin", "admin_master"):
            raise HTTPException(status_code=403, detail="Apenas admins podem criar operadores.")

        existing = AuthRepository.get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado.")

        password_hash = Hash.hash_password(data.password)
        user = AuthRepository.create_user(
            db=db,
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            role="operador",
            invited_by_id=creator.id,
        )
        user.is_email_verified = True
        user.age_verified = True
        if getattr(data, "restaurant_id", None):
            user.restaurant_id = data.restaurant_id
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_operadores(db, requester):
        """Lista operadores - admin e master podem ver"""
        from app.domain.auth.models.user_model import User
        if requester.role not in ("admin", "admin_master"):
            raise HTTPException(status_code=403, detail="Apenas admins podem listar operadores.")
        return db.query(User).filter(User.role == "operador", User.status == "active").order_by(User.created_at.desc()).all()

    @staticmethod
    def delete_operador(db, operador_id: int, requester):
        """Desativa conta de operador"""
        if requester.role not in ("admin", "admin_master"):
            raise HTTPException(status_code=403, detail="Apenas admins podem remover operadores.")
        operador = AuthRepository.get_user_by_id(db, operador_id)
        if not operador or operador.role != "operador":
            raise HTTPException(status_code=404, detail="Operador não encontrado.")
        operador.status = "inactive"
        operador.deactivated_by_id = requester.id
        operador.deactivated_at = datetime.utcnow()
        db.commit()
        invalidate_user_cache(operador_id)
        return {"message": "Operador desativado com sucesso."}
