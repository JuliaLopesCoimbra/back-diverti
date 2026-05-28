#!/usr/bin/env python3
"""
Cria um evento diretamente no banco de dados do projeto.

Uso basico:
    python create_event.py --title "Meu Evento" --starts-at "2026-04-10T20:00" --ends-at "2026-04-11T06:00"

Exemplo com mais campos:
    python create_event.py ^
      --title "Rock World 2026" ^
      --description "Evento de teste" ^
      --location "Sambodromo" ^
      --starts-at "2026-04-10T20:00" ^
      --ends-at "2026-04-11T06:00" ^
      --event-dates "2026-04-10,2026-04-11" ^
      --meeting-point-location "Portao A" ^
      --meeting-point-schedule "[{\"days\":[10,11],\"start_time\":\"18:00\",\"end_time\":\"22:00\"}]"

Observacoes:
    - O script le automaticamente o arquivo .env da pasta back
    - Se voce nao passar --admin-email, ele usa o primeiro usuario admin_master/subadmin encontrado
    - Nao faz upload de imagens; cria apenas os campos textuais e datas
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Any, Optional


BACK_DIR = Path(__file__).resolve().parent
ENV_FILE = BACK_DIR / ".env"


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise FileNotFoundError(f"Arquivo de ambiente nao encontrado: {env_path}")

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(ENV_FILE)
sys.path.insert(0, str(BACK_DIR))

from sqlalchemy.orm import Session  # noqa: E402
from app.config.admin_db import AdminSessionLocal  # noqa: E402
from app.config.auth_db import SessionLocal  # noqa: E402
from app.domain.admin.models.news_image_model import NewsImage  # noqa: F401, E402
from app.domain.admin.models.news_model import NewsPost  # noqa: F401, E402
from app.domain.admin.models.event_model import Event  # noqa: E402
from app.domain.auth.models.user_model import User  # noqa: E402


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Data invalida: {value}. Use YYYY-MM-DDTHH:MM ou um ISO valido."
        ) from exc


def parse_time(value: Optional[str]) -> Optional[time]:
    if not value:
        return None

    try:
        return time.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"Horario invalido: {value}. Use HH:MM.") from exc


def parse_schedule(value: Optional[str]) -> Any:
    if not value:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("meeting-point-schedule precisa ser um JSON valido.") from exc


def get_admin_user(auth_db: Session, admin_email: Optional[str]) -> User:
    query = auth_db.query(User).filter(User.role.in_(["admin_master", "subadmin"]))

    if admin_email:
        user = query.filter(User.email == admin_email.strip().lower()).first()
        if not user:
            raise ValueError(f"Nenhum admin/subadmin encontrado com email: {admin_email}")
        return user

    user = query.order_by(User.id.asc()).first()
    if not user:
        raise ValueError("Nenhum usuario admin_master/subadmin foi encontrado.")
    return user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cria um evento no banco do projeto.")
    parser.add_argument("--title", required=True, help="Titulo do evento.")
    parser.add_argument("--description", help="Descricao do evento.")
    parser.add_argument("--location", help="Local do evento.")
    parser.add_argument("--starts-at", help="Inicio no formato YYYY-MM-DDTHH:MM.")
    parser.add_argument("--ends-at", help="Fim no formato YYYY-MM-DDTHH:MM.")
    parser.add_argument("--event-dates", help='Datas extras, ex: "2026-04-10,2026-04-11".')
    parser.add_argument("--line-up", help="Line-up em texto.")
    parser.add_argument("--spotify-playlist-url", help="URL da playlist.")
    parser.add_argument("--van-arrival-time-start", help="HH:MM")
    parser.add_argument("--van-arrival-time-end", help="HH:MM")
    parser.add_argument("--van-departure-time-start", help="HH:MM")
    parser.add_argument("--van-departure-time-end", help="HH:MM")
    parser.add_argument("--meeting-point-location", help="Local do meeting point.")
    parser.add_argument(
        "--meeting-point-schedule",
        help='JSON do schedule, ex: \'[{"days":[10,11],"start_time":"18:00","end_time":"22:00"}]\'',
    )
    parser.add_argument(
        "--admin-email",
        help="Email do admin/subadmin que sera usado como criador do evento.",
    )
    parser.add_argument(
        "--inactive",
        action="store_true",
        help="Cria o evento com is_active=False.",
    )
    parser.add_argument(
        "--requires-post-approval",
        choices=["true", "false"],
        default="true",
        help="Define requires_post_approval. Padrao: true.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    starts_at = parse_datetime(args.starts_at)
    ends_at = parse_datetime(args.ends_at)

    if starts_at and ends_at and ends_at <= starts_at:
        raise ValueError("ends-at precisa ser maior que starts-at.")

    auth_db: Optional[Session] = None
    admin_db: Optional[Session] = None

    try:
        auth_db = SessionLocal()
        admin_user = get_admin_user(auth_db, args.admin_email)

        admin_db = AdminSessionLocal()
        event = Event(
            title=args.title.strip(),
            description=args.description.strip() if args.description else None,
            location=args.location.strip() if args.location else None,
            starts_at=starts_at,
            ends_at=ends_at,
            event_dates=args.event_dates.strip() if args.event_dates else None,
            line_up=args.line_up.strip() if args.line_up else None,
            spotify_playlist_url=(
                args.spotify_playlist_url.strip() if args.spotify_playlist_url else None
            ),
            van_arrival_time_start=parse_time(args.van_arrival_time_start),
            van_arrival_time_end=parse_time(args.van_arrival_time_end),
            van_departure_time_start=parse_time(args.van_departure_time_start),
            van_departure_time_end=parse_time(args.van_departure_time_end),
            meeting_point_location=(
                args.meeting_point_location.strip() if args.meeting_point_location else None
            ),
            meeting_point_schedule=parse_schedule(args.meeting_point_schedule),
            is_active=not args.inactive,
            requires_post_approval=args.requires_post_approval == "true",
            created_by_id=admin_user.id,
        )

        admin_db.add(event)
        admin_db.commit()
        admin_db.refresh(event)

        print("Evento criado com sucesso.")
        print(json.dumps(
            {
                "id": event.id,
                "title": event.title,
                "created_by_id": event.created_by_id,
                "is_active": event.is_active,
                "requires_post_approval": event.requires_post_approval,
                "starts_at": event.starts_at.isoformat() if event.starts_at else None,
                "ends_at": event.ends_at.isoformat() if event.ends_at else None,
            },
            ensure_ascii=True,
            indent=2,
        ))
        return 0
    except Exception as exc:
        if admin_db:
            admin_db.rollback()
        print(f"Erro ao criar evento: {exc}", file=sys.stderr)
        return 1
    finally:
        if auth_db:
            auth_db.close()
        if admin_db:
            admin_db.close()


if __name__ == "__main__":
    raise SystemExit(main())
