from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.domain.users.models.downloaded_photo_model import DownloadedPhoto

class DownloadedPhotoRepository:
    @staticmethod
    def create(db: Session, data: dict) -> DownloadedPhoto:
        downloaded_photo = DownloadedPhoto(**data)
        db.add(downloaded_photo)
        db.commit()
        db.refresh(downloaded_photo)
        return downloaded_photo

    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 100, offset: int = 0):
        return (
            db.query(DownloadedPhoto)
            .filter(DownloadedPhoto.user_id == user_id)
            .order_by(desc(DownloadedPhoto.downloaded_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_by_user(db: Session, user_id: int) -> int:
        return db.query(DownloadedPhoto).filter(DownloadedPhoto.user_id == user_id).count()

    @staticmethod
    def get_by_user_and_url(db: Session, user_id: int, image_url: str):
        """Verifica se o usuário já baixou esta imagem"""
        return (
            db.query(DownloadedPhoto)
            .filter(
                DownloadedPhoto.user_id == user_id,
                DownloadedPhoto.image_url == image_url
            )
            .first()
        )

