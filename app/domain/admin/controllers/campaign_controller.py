# app/domain/admin/controllers/campaign_controller.py

from sqlalchemy.orm import Session
from typing import List

from app.domain.admin.schemas.campaign_schema import CampaignCreateRequest, CampaignResponse, PatrocinadorWithCampaigns
from app.domain.admin.services.campaign_service import CampaignService
from app.domain.auth.models.user_model import User


class CampaignController:

    @staticmethod
    def create_campaign(
        db_admin: Session,
        db_auth: Session,
        data: CampaignCreateRequest,
        current_user: User
    ) -> CampaignResponse:
        """Cria uma campanha. admin_master cria em nome de si mesmo como patrocinador_id
        se não for patrocinador, mas normalmente patrocinador cria para si mesmo."""
        patrocinador_id = current_user.id
        campaign = CampaignService.create_campaign(db_admin, db_auth, patrocinador_id, data)
        return CampaignResponse.model_validate(campaign)

    @staticmethod
    def list_my_campaigns(
        db_admin: Session,
        current_user: User,
        limit: int = 50,
        offset: int = 0
    ) -> List[CampaignResponse]:
        campaigns = CampaignService.list_my_campaigns(db_admin, current_user.id, limit, offset)
        return [CampaignResponse.model_validate(c) for c in campaigns]

    @staticmethod
    def list_all_grouped(
        db_admin: Session,
        db_auth: Session
    ) -> List[PatrocinadorWithCampaigns]:
        return CampaignService.list_all_campaigns_grouped(db_admin, db_auth)
