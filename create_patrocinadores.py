#!/usr/bin/env python3
"""
Cria usuarios patrocinadores diretamente no banco auth_db.

Uso:
    python create_patrocinadores.py
    python create_patrocinadores.py --password "OutraSenha@123"
    python create_patrocinadores.py --dry-run   # mostra o que seria criado sem salvar
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACK_DIR = Path(__file__).resolve().parent
ENV_FILE = BACK_DIR / ".env"


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise FileNotFoundError(f"Arquivo .env nao encontrado: {env_path}")
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(ENV_FILE)
sys.path.insert(0, str(BACK_DIR))

from app.config.auth_db import SessionLocal          # noqa: E402
from app.domain.auth.models.user_model import User   # noqa: E402
from app.core.security.hashing import Hash           # noqa: E402

PATROCINADORES = [
    {"name": "Globoplay",    "email": "globoplay@patrocinador.diverti.com.br"},
    {"name": "Brahma",       "email": "brahma@patrocinador.diverti.com.br"},
    {"name": "Sicoob",       "email": "sicoob@patrocinador.diverti.com.br"},
    {"name": "Ballantine's", "email": "ballantines@patrocinador.diverti.com.br"},
    {"name": "Volkswagen",   "email": "volkswagen@patrocinador.diverti.com.br"},
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria patrocinadores no banco.")
    parser.add_argument("--password", default="Diverti@2026", help="Senha padrao para todos.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria criado sem salvar.")
    args = parser.parse_args()

    password_hash = Hash.hash_password(args.password)

    if args.dry_run:
        print("[DRY-RUN] Patrocinadores que seriam criados:")
        for p in PATROCINADORES:
            print(f"  - {p['name']} <{p['email']}> (senha: {args.password})")
        return 0

    db = SessionLocal()
    created = []
    skipped = []
    try:
        for p in PATROCINADORES:
            existing = db.query(User).filter(User.email == p["email"]).first()
            if existing:
                skipped.append(p)
                print(f"[SKIP] {p['name']} <{p['email']}> ja existe (id={existing.id})")
                continue

            user = User(
                name=p["name"],
                email=p["email"],
                password_hash=password_hash,
                role="patrocinador",
                is_email_verified=True,
                age_verified=True,
                lgpd_accepted=True,
                status="active",
            )
            db.add(user)
            db.flush()  # obtem o id antes do commit
            created.append({"id": user.id, "name": p["name"], "email": p["email"]})
            print(f"[OK] {p['name']} <{p['email']}> -> id={user.id}")

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[ERRO] {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print()
    print(json.dumps(
        {
            "created": created,
            "skipped": [{"name": p["name"], "email": p["email"]} for p in skipped],
            "password": args.password,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
