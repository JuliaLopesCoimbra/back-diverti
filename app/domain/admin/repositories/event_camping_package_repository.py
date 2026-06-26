from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.admin.models.event_camping_package_model import EventCampingPackage


class EventCampingPackageRepository:
    @staticmethod
    def get_by_event(db: Session, event_id: int) -> list[EventCampingPackage]:
        return (
            db.query(EventCampingPackage)
            .filter(EventCampingPackage.event_id == event_id, EventCampingPackage.deleted_at.is_(None))
            .order_by(EventCampingPackage.sort_order, EventCampingPackage.created_at)
            .all()
        )

    @staticmethod
    def get_active_by_event(db: Session, event_id: int) -> list[EventCampingPackage]:
        return (
            db.query(EventCampingPackage)
            .filter(
                EventCampingPackage.event_id == event_id,
                EventCampingPackage.is_active.is_(True),
                EventCampingPackage.deleted_at.is_(None),
            )
            .order_by(EventCampingPackage.sort_order, EventCampingPackage.created_at)
            .all()
        )

    @staticmethod
    def get(db: Session, package_id: int) -> Optional[EventCampingPackage]:
        return db.query(EventCampingPackage).filter(
            EventCampingPackage.id == package_id,
            EventCampingPackage.deleted_at.is_(None),
        ).first()

    @staticmethod
    def create(db: Session, data: dict) -> EventCampingPackage:
        pkg = EventCampingPackage(**data)
        db.add(pkg)
        db.commit()
        db.refresh(pkg)
        return pkg

    @staticmethod
    def update(db: Session, pkg: EventCampingPackage, data: dict) -> EventCampingPackage:
        for key, value in data.items():
            if value is not None or key in ("days", "badge", "badge_color", "price_label", "period"):
                setattr(pkg, key, value)
        db.commit()
        db.refresh(pkg)
        return pkg

    @staticmethod
    def soft_delete(db: Session, pkg: EventCampingPackage, deleted_by_id: int) -> None:
        pkg.deleted_at = datetime.now(timezone.utc)
        pkg.deleted_by_id = deleted_by_id
        db.commit()
