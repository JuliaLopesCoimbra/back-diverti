# app/domain/admin/repositories/campaign_repository.py

from sqlalchemy.orm import Session
from typing import Optional
from app.domain.admin.models.campaign_model import Campaign

class CampaignRepository:

    @staticmethod
    def create_campaign(db: Session, patrocinador_id: int, data: dict) -> Campaign:
        campaign = Campaign(patrocinador_id=patrocinador_id, **data)
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def list_campaigns_by_patrocinador(
        db: Session,
        patrocinador_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> list[Campaign]:
        limit = min(limit, 200)
        return (
            db.query(Campaign)
            .filter(Campaign.patrocinador_id == patrocinador_id)
            .order_by(Campaign.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_campaign_by_id(db: Session, campaign_id: int) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

    @staticmethod
    def list_all_campaigns(db: Session, limit: int = 200, offset: int = 0) -> list[Campaign]:
        limit = min(limit, 500)
        return (
            db.query(Campaign)
            .order_by(Campaign.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_pending_campaigns(db: Session) -> list[Campaign]:
        return (
            db.query(Campaign)
            .filter(Campaign.status == "pending")
            .order_by(Campaign.created_at.desc())
            .all()
        )

    @staticmethod
    def update_campaign_status(db: Session, campaign_id: int, status: str) -> Optional[Campaign]:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return None
        campaign.status = status
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def list_campaigns_grouped_by_patrocinador(db: Session) -> dict:
        """Returns a dict: {patrocinador_id: [campaigns]}"""
        campaigns = (
            db.query(Campaign)
            .order_by(Campaign.patrocinador_id, Campaign.created_at.desc())
            .all()
        )
        grouped: dict[int, list[Campaign]] = {}
        for campaign in campaigns:
            pid = campaign.patrocinador_id
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(campaign)
        return grouped
