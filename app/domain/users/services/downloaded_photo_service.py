from app.domain.users.repositories.downloaded_photo_repository import DownloadedPhotoRepository
from app.domain.users.schemas.downloaded_photo_schema import DownloadedPhotoResponse
from typing import List

class DownloadedPhotoService:
    @staticmethod
    def create_downloaded_photo(db, user_id: int, image_url: str, event_id: int = None, event_name: str = None, similarity: str = None):
        # Verifica se o usuário já baixou esta imagem antes
        existing = DownloadedPhotoRepository.get_by_user_and_url(db, user_id, image_url)
        
        if existing:
            # Se já existe, apenas atualiza a data de download e outras informações se necessário
            from datetime import datetime, timezone
            existing.downloaded_at = datetime.now(timezone.utc)
            if event_id is not None:
                existing.event_id = event_id
            if event_name is not None:
                existing.event_name = event_name
            if similarity is not None:
                existing.similarity = similarity
            db.commit()
            db.refresh(existing)
            return existing
        
        # Se não existe, cria um novo registro
        data = {
            "user_id": user_id,
            "image_url": image_url,
            "event_id": event_id,
            "event_name": event_name,
            "similarity": similarity,
        }
        return DownloadedPhotoRepository.create(db, data)

    @staticmethod
    def get_user_downloaded_photos(db, user_id: int, limit: int = 100, offset: int = 0) -> List[DownloadedPhotoResponse]:
        photos = DownloadedPhotoRepository.get_by_user(db, user_id, limit, offset)
        return [DownloadedPhotoResponse.model_validate(photo) for photo in photos]

