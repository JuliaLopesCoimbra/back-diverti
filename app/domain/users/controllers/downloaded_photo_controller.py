from app.domain.users.services.downloaded_photo_service import DownloadedPhotoService
from app.domain.users.schemas.downloaded_photo_schema import DownloadedPhotoResponse, CreateDownloadedPhotoRequest
from typing import List

class DownloadedPhotoController:
    @staticmethod
    def create_downloaded_photo(db, user_id: int, body: CreateDownloadedPhotoRequest) -> DownloadedPhotoResponse:
        photo = DownloadedPhotoService.create_downloaded_photo(
            db=db,
            user_id=user_id,
            image_url=body.image_url,
            event_id=body.event_id,
            event_name=body.event_name,
            similarity=body.similarity,
        )
        return DownloadedPhotoResponse.model_validate(photo)

    @staticmethod
    def get_user_downloaded_photos(db, user_id: int, limit: int = 100, offset: int = 0) -> List[DownloadedPhotoResponse]:
        return DownloadedPhotoService.get_user_downloaded_photos(db, user_id, limit, offset)




