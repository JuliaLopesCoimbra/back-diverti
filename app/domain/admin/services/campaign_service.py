# app/domain/admin/services/campaign_service.py

from sqlalchemy.orm import Session
from typing import List

from app.domain.admin.models.campaign_model import Campaign
from app.domain.admin.repositories.campaign_repository import CampaignRepository
from app.domain.admin.schemas.campaign_schema import CampaignCreateRequest, PatrocinadorWithCampaigns, CampaignResponse
from app.domain.auth.models.user_model import User


class CampaignService:

    @staticmethod
    def create_campaign(
        db_admin: Session,
        db_auth: Session,
        patrocinador_id: int,
        data: CampaignCreateRequest
    ) -> Campaign:
        """Verifica que o usuário é patrocinador no auth DB e cria a campanha."""
        user = db_auth.query(User).filter(User.id == patrocinador_id).first()
        if not user:
            raise ValueError("Patrocinador não encontrado.")
        if user.role != "patrocinador":
            raise ValueError("O usuário não tem o perfil de patrocinador.")

        campaign_data = data.model_dump(exclude_unset=False)
        return CampaignRepository.create_campaign(db_admin, patrocinador_id, campaign_data)

    @staticmethod
    def list_my_campaigns(
        db: Session,
        patrocinador_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Campaign]:
        return CampaignRepository.list_campaigns_by_patrocinador(db, patrocinador_id, limit, offset)

    @staticmethod
    def list_pending_campaigns(db_admin: Session, db_auth: Session) -> List[PatrocinadorWithCampaigns]:
        """Retorna campanhas pendentes com dados do patrocinador."""
        campaigns = CampaignRepository.list_pending_campaigns(db_admin)
        if not campaigns:
            return []
        patrocinador_ids = list({c.patrocinador_id for c in campaigns})
        users = db_auth.query(User).filter(User.id.in_(patrocinador_ids)).all()
        users_by_id = {u.id: u for u in users}
        grouped: dict = {}
        for c in campaigns:
            pid = c.patrocinador_id
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(c)
        result = []
        for pid, clist in grouped.items():
            user = users_by_id.get(pid)
            result.append(PatrocinadorWithCampaigns(
                patrocinador_id=pid,
                patrocinador_name=user.name if user else None,
                patrocinador_email=user.email if user else None,
                campaigns=[CampaignResponse.model_validate(c) for c in clist],
            ))
        return result

    @staticmethod
    def update_campaign_status(db_admin: Session, campaign_id: int, status: str) -> CampaignResponse:
        allowed = {"active", "pending", "paused", "finished", "cancelled", "recusado"}
        if status not in allowed:
            raise ValueError(f"Status inválido: {status}")
        campaign = CampaignRepository.update_campaign_status(db_admin, campaign_id, status)
        if not campaign:
            raise ValueError("Campanha não encontrada.")
        return CampaignResponse.model_validate(campaign)

    @staticmethod
    def list_all_campaigns_grouped(
        db_admin: Session,
        db_auth: Session
    ) -> List[PatrocinadorWithCampaigns]:
        """Retorna todas as campanhas agrupadas por patrocinador com dados do usuário."""
        grouped = CampaignRepository.list_campaigns_grouped_by_patrocinador(db_admin)

        if not grouped:
            return []

        patrocinador_ids = list(grouped.keys())
        users = db_auth.query(User).filter(User.id.in_(patrocinador_ids)).all()
        users_by_id = {u.id: u for u in users}

        result = []
        for pid, campaigns in grouped.items():
            user = users_by_id.get(pid)
            result.append(
                PatrocinadorWithCampaigns(
                    patrocinador_id=pid,
                    patrocinador_name=user.name if user else None,
                    patrocinador_email=user.email if user else None,
                    campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
                )
            )

        return result
