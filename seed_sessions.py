"""
Cria sessoes para todos os estandes do evento 2.
Data: 2026-09-04, horarios de 11:00 as 22:00 (1 em 1 hora), capacidade 100.
Usa SQL puro para evitar problemas com relacionamentos ORM.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.config.settings import settings
from sqlalchemy import create_engine, text

STAND_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
SESSION_DATE = "2026-09-04"
START_HOURS = list(range(11, 23))  # 11 ate 22 inclusive
CAPACITY = 100
CREATED_BY_ID = 1

def main():
    engine = create_engine(
        settings.ADMIN_DATABASE_URL,
        connect_args={"sslmode": "require"},
    )
    created = 0
    skipped = 0

    with engine.begin() as conn:
        for stand_id in STAND_IDS:
            for hour in START_HOURS:
                start_time = f"{hour:02d}:00:00"
                end_time = f"{hour + 1:02d}:00:00" if hour < 22 else None

                row = conn.execute(text("""
                    SELECT id FROM event_stand_sessions
                    WHERE stand_id = :stand_id
                      AND session_date = :session_date
                      AND start_time = :start_time
                      AND deleted_at IS NULL
                """), {"stand_id": stand_id, "session_date": SESSION_DATE, "start_time": start_time}).fetchone()

                if row:
                    skipped += 1
                    continue

                conn.execute(text("""
                    INSERT INTO event_stand_sessions
                        (stand_id, session_date, start_time, end_time, capacity, status, created_by_id)
                    VALUES
                        (:stand_id, :session_date, :start_time, :end_time, :capacity, 'active', :created_by_id)
                """), {
                    "stand_id": stand_id,
                    "session_date": SESSION_DATE,
                    "start_time": start_time,
                    "end_time": end_time,
                    "capacity": CAPACITY,
                    "created_by_id": CREATED_BY_ID,
                })
                created += 1

    print(f"OK: {created} sessoes criadas, {skipped} ja existiam.")

if __name__ == "__main__":
    main()
