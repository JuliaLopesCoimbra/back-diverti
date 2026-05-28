from app.domain.admin.repositories.samba_school_repository import SambaSchoolRepository
from app.domain.admin.repositories.music_lyrics_repository import MusicLyricsRepository
from app.domain.admin.repositories.event_repository import EventRepository

class MusicLyricsService:

    @staticmethod
    def create(db, data, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem criar músicas")

        samba_school = SambaSchoolRepository.get_by_id(db, data["samba_school_id"])
        if not samba_school:
            raise ValueError("Escola de samba não encontrada")

        # Verifica se já existe uma música para esta escola de samba
        existing_music = MusicLyricsRepository.get_by_samba_school(db, data["samba_school_id"])
        if existing_music:
            raise ValueError("Esta escola de samba já possui uma música cadastrada. Use o endpoint de atualização para modificar.")

        # Adiciona created_by_id ao data
        data["created_by_id"] = user.id
        
        return MusicLyricsRepository.create(db, data)

    @staticmethod
    def get_by_samba_school(db, samba_school_id: int):
        samba_school = SambaSchoolRepository.get_by_id(db, samba_school_id)
        if not samba_school:
            raise ValueError("Escola de samba não encontrada")

        music = MusicLyricsRepository.get_by_samba_school(db, samba_school_id)
        return music

    @staticmethod
    def list_by_event(db, event_id: int, limit: int = 50, offset: int = 0):
        event = EventRepository.get_by_id(db, event_id)
        if not event:
            raise ValueError("Evento não encontrado")

        return MusicLyricsRepository.list_by_event(db, event_id, limit=limit, offset=offset)

    @staticmethod
    def get_by_id(db, music_id: int):
        music = MusicLyricsRepository.get_by_id(db, music_id)
        if not music:
            raise ValueError("Música/Letra não encontrada")
        return music

    @staticmethod
    def update(db, music_id: int, data: dict, user):
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem editar músicas/letras")

        music = MusicLyricsRepository.get_by_id(db, music_id)
        if not music:
            raise ValueError("Música/Letra não encontrada")

        # Remove samba_school_id dos dados se presente (não deve ser alterado)
        data.pop("samba_school_id", None)
        
        # Adiciona updated_by_id ao data
        data["updated_by_id"] = user.id

        return MusicLyricsRepository.update(db, music, data)

    @staticmethod
    def delete(db, music_id: int, user):
        from datetime import datetime
        
        if user.role not in ["admin_master", "subadmin"]:
            raise PermissionError("Apenas admin master ou subadmin podem deletar músicas/letras")

        music = MusicLyricsRepository.get_by_id(db, music_id)
        if not music:
            raise ValueError("Música/Letra não encontrada")

        # Verifica se já foi deletado
        if music.deleted_at is not None:
            raise ValueError("Música/Letra já foi deletada")

        # Soft delete: marca como deletado sem remover do banco
        music.deleted_at = datetime.utcnow()
        music.deleted_by_id = user.id
        
        db.commit()
        db.refresh(music)
        
        return music