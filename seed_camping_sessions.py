"""
Cria sessoes de camping com 15 min de intervalo entre cada horario.
Padrao: 08:00-09:00, 09:15-10:15, 10:30-11:30, ... ate o fim caber antes das 22:00

Configurar antes de rodar:
  EVENT_ID      -> id do evento
  SESSION_DATE  -> data do camping (YYYY-MM-DD)
  DELETE_FIRST  -> True para apagar sessoes existentes das vagas antes de criar
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.config.settings import settings
from sqlalchemy import create_engine, text

# ── Configurar aqui ─────────────────────────────────────────────────────────
EVENT_ID      = 2
SESSION_DATE  = "2026-09-05"
DELETE_FIRST  = True      # apaga os horarios existentes antes de criar os novos
CREATED_BY_ID = 1
# ────────────────────────────────────────────────────────────────────────────

SESSION_START  = "08:00"
SESSION_END    = "22:00"
DURATION_MIN   = 60   # duracao de cada horario em minutos
GAP_MIN        = 15   # intervalo entre o fim de um e o inicio do proximo


def build_slots(start_str: str, end_limit_str: str, duration_min: int, gap_min: int):
    """Gera lista de (label, inicio, fim) respeitando o limite de horario."""
    fmt = "%H:%M"
    current = datetime.strptime(start_str, fmt)
    limit   = datetime.strptime(end_limit_str, fmt)
    duration = timedelta(minutes=duration_min)
    gap      = timedelta(minutes=gap_min)

    slots = []
    while True:
        end = current + duration
        if end > limit:
            break
        slots.append(f"{current.strftime(fmt)} - {end.strftime(fmt)}")
        current = end + gap
    return slots


def main():
    slots = build_slots(SESSION_START, SESSION_END, DURATION_MIN, GAP_MIN)
    print(f"Horarios gerados ({len(slots)}):")
    for s in slots:
        print(f"  {s}")
    print()

    engine = create_engine(
        settings.ADMIN_DATABASE_URL,
        connect_args={"sslmode": "require"},
    )

    with engine.begin() as conn:
        areas = conn.execute(text("""
            SELECT id, name FROM event_camping_areas
            WHERE event_id = :event_id
              AND deleted_at IS NULL
            ORDER BY id
        """), {"event_id": EVENT_ID}).fetchall()

        if not areas:
            print(f"Nenhuma vaga encontrada para o evento {EVENT_ID}.")
            return

        area_ids = [a.id for a in areas]
        print(f"Encontradas {len(areas)} vagas: {[a.name for a in areas]}")

        if DELETE_FIRST:
            result = conn.execute(text("""
                DELETE FROM event_camping_sessions
                WHERE area_id = ANY(:ids)
            """), {"ids": area_ids})
            print(f"Removidas {result.rowcount} sessoes existentes.\n")

        created = 0
        for area in areas:
            for label in slots:
                conn.execute(text("""
                    INSERT INTO event_camping_sessions
                        (area_id, label, check_in_date, check_out_date, capacity, status, created_by_id)
                    VALUES
                        (:area_id, :label, :date, :date, 1, 'active', :created_by)
                """), {
                    "area_id": area.id,
                    "label": label,
                    "date": SESSION_DATE,
                    "created_by": CREATED_BY_ID,
                })
                created += 1

            print(f"  {area.name} (id={area.id}): {len(slots)} horarios criados")

    print(f"\nPronto: {created} sessoes criadas no total.")


if __name__ == "__main__":
    main()
