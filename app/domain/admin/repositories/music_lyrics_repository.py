from sqlalchemy.orm import Session
from app.domain.admin.models.music_lyrics_model import MusicLyrics

class MusicLyricsRepository:

    @staticmethod
    def create(db: Session, data: dict):
        music = MusicLyrics(**data)
        db.add(music)
        db.commit()
        db.refresh(music)
        return music

    @staticmethod
    def get_by_samba_school(db: Session, samba_school_id: int, include_deleted: bool = False):
        """Obtém a música/letra de uma escola de samba (uma por escola)"""
        query = db.query(MusicLyrics).filter(MusicLyrics.samba_school_id == samba_school_id)
        if not include_deleted:
            query = query.filter(MusicLyrics.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def list_by_event(db: Session, event_id: int, include_deleted: bool = False, limit: int = 50, offset: int = 0):
        """Lista letras de música de um evento através das escolas de samba com paginação obrigatória"""
        from app.domain.admin.models.samba_school_model import SambaSchool
        limit = min(limit, 100)  # Máximo de 100 por requisição
        query = db.query(MusicLyrics).join(SambaSchool).filter(SambaSchool.event_id == event_id)
        if not include_deleted:
            query = query.filter(MusicLyrics.deleted_at.is_(None)).filter(SambaSchool.deleted_at.is_(None))
        return query.order_by(MusicLyrics.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def get_by_id(db: Session, music_id: int, include_deleted: bool = False):
        query = db.query(MusicLyrics).filter(MusicLyrics.id == music_id)
        if not include_deleted:
            query = query.filter(MusicLyrics.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def update(db: Session, music: MusicLyrics, data: dict):
        from datetime import datetime
        
        for key, value in data.items():
            if value is not None:
                setattr(music, key, value)
        
        # Atualiza updated_at automaticamente se não foi fornecido
        if 'updated_at' not in data:
            music.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(music)
        return music

    @staticmethod
    def delete(db: Session, music):
        """Método legado - não usar. Use MusicLyricsService.delete para soft delete."""
        # Este método não deve ser usado mais, mas mantido para compatibilidade
        db.delete(music)
        db.commit()
