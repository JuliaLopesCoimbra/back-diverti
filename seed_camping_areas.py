"""
Apaga todas as vagas de camping de um evento e recria com a nomenclatura
1A, 1B, ... 1J, 2A, ... 5J (50 vagas no total).

Configurar antes de rodar:
  EVENT_ID     -> id do evento
  ADMIN_ID     -> id do admin que sera marcado como created_by_id
  DELETE_FIRST -> True para apagar vagas existentes (e todas as sessoes/bookings vinculadas)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.config.settings import settings
from sqlalchemy import create_engine, text

# ── Configurar aqui ─────────────────────────────────────────────────────────
EVENT_ID     = 2
ADMIN_ID     = 1
DELETE_FIRST = True
# ────────────────────────────────────────────────────────────────────────────

LETTERS = "ABCDEFGHIJ"   # 10 letras por número


def spot_name(idx: int) -> str:
    num    = idx // 10 + 1       # 1–5
    letter = LETTERS[idx % 10]   # A–J
    return f"{num}{letter}"


def spot_position(idx: int) -> tuple:
    col = idx % 10
    row = idx // 10
    x = round(0.05 + col * 0.09, 4)   # 0.05 → 0.86
    y = round(0.10 + row * 0.20, 4)   # 0.10 → 0.90
    return x, y


def main():
    names = [spot_name(i) for i in range(50)]
    print(f"Vagas a criar ({len(names)}): {', '.join(names)}\n")

    engine = create_engine(
        settings.ADMIN_DATABASE_URL,
        connect_args={"sslmode": "require"},
    )

    with engine.begin() as conn:
        if DELETE_FIRST:
            # Busca IDs das áreas existentes do evento
            rows = conn.execute(text("""
                SELECT id FROM event_camping_areas
                WHERE event_id = :event_id
                  AND deleted_at IS NULL
            """), {"event_id": EVENT_ID}).fetchall()

            if rows:
                area_ids = [r.id for r in rows]
                print(f"Removendo {len(area_ids)} vagas existentes e tudo vinculado...")

                # Busca IDs das sessões dessas áreas
                session_rows = conn.execute(text("""
                    SELECT id FROM event_camping_sessions
                    WHERE area_id = ANY(:ids)
                """), {"ids": area_ids}).fetchall()

                if session_rows:
                    session_ids = [r.id for r in session_rows]

                    # Entradas de check-in
                    r = conn.execute(text("""
                        DELETE FROM event_camping_entries
                        WHERE booking_id IN (
                            SELECT id FROM event_camping_bookings
                            WHERE camping_session_id = ANY(:ids)
                        )
                    """), {"ids": session_ids})
                    print(f"  {r.rowcount} entradas removidas")

                    # Bookings
                    r = conn.execute(text("""
                        DELETE FROM event_camping_bookings
                        WHERE camping_session_id = ANY(:ids)
                    """), {"ids": session_ids})
                    print(f"  {r.rowcount} reservas removidas")

                    # Sessões
                    r = conn.execute(text("""
                        DELETE FROM event_camping_sessions
                        WHERE area_id = ANY(:ids)
                    """), {"ids": area_ids})
                    print(f"  {r.rowcount} sessoes removidas")

                # Áreas
                r = conn.execute(text("""
                    DELETE FROM event_camping_areas
                    WHERE event_id = :event_id
                """), {"event_id": EVENT_ID})
                print(f"  {r.rowcount} vagas removidas\n")
            else:
                print("Nenhuma vaga existente para remover.\n")

        # Cria as 50 novas vagas
        created = 0
        for i in range(50):
            name = spot_name(i)
            x, y = spot_position(i)
            conn.execute(text("""
                INSERT INTO event_camping_areas
                    (event_id, name, total_spots, x_position, y_position, created_by_id)
                VALUES
                    (:event_id, :name, 1, :x, :y, :admin_id)
            """), {
                "event_id": EVENT_ID,
                "name":     name,
                "x":        x,
                "y":        y,
                "admin_id": ADMIN_ID,
            })
            created += 1

        print(f"Criadas {created} vagas: {', '.join(names)}")

    print("\nPronto!")


if __name__ == "__main__":
    main()
