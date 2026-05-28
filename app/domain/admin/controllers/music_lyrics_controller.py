from app.domain.admin.services.music_lyrics_service import MusicLyricsService

class MusicLyricsController:

    @staticmethod
    def create(db, data, user):
        return MusicLyricsService.create(db, data, user)

    @staticmethod
    def get_by_samba_school(db, samba_school_id: int):
        return MusicLyricsService.get_by_samba_school(db, samba_school_id)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        return MusicLyricsService.list_by_event(db, event_id, limit, offset)

    @staticmethod
    def get_by_id(db, music_id: int):
        return MusicLyricsService.get_by_id(db, music_id)

    @staticmethod
    def update(db, music_id: int, data: dict, user):
        return MusicLyricsService.update(db, music_id, data, user)

    @staticmethod
    def delete(db, music_id: int, user):
        return MusicLyricsService.delete(db, music_id, user)