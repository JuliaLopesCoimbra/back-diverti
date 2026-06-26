"""
Run once to seed restaurant and menu data.
  cd back
  python seed_food.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.config.admin_db import admin_engine
from sqlalchemy import text

with admin_engine.begin() as conn:
    # find event
    event_row = conn.execute(text("SELECT id FROM events ORDER BY id LIMIT 1")).fetchone()
    if not event_row:
        print("ERRO: Nenhum evento encontrado. Crie um evento primeiro.")
        sys.exit(1)
    event_id = event_row[0]
    print(f"OK  event_id={event_id}")

    # find admin
    admin_row = conn.execute(text("SELECT id FROM users WHERE role IN ('admin','admin_master') ORDER BY id LIMIT 1")).fetchone()
    admin_id = admin_row[0] if admin_row else 1

    # guard
    existing = conn.execute(text(
        "SELECT COUNT(*) FROM restaurants WHERE event_id=:eid AND deleted_at IS NULL"
    ), {"eid": event_id}).scalar()
    if existing >= 2:
        print(f"INFO  Ja existem {existing} restaurante(s) para o evento {event_id}. Seed ignorado.")
        sys.exit(0)

    # ── Restaurant 1 ────────────────────────────────────────────────────────
    r1 = conn.execute(text("""
        INSERT INTO restaurants (event_id, name, description, is_active, created_by_id)
        VALUES (:eid, :name, :desc, true, :aid)
        RETURNING id
    """), {
        "eid": event_id,
        "name": "Marmitaria Diverti",
        "desc": "Marmitas caprichadas com opcoes de proteinas, acompanhamentos e bebidas",
        "aid": admin_id,
    }).scalar()

    items_r1 = [
        ("Marmita - Frango Grelhado",   "Peito de frango grelhado temperado - arroz, feijao, salada e batata frita",  "32.90", "Marmitas"),
        ("Marmita - Picanha",           "Picanha ao ponto na chapa - arroz, feijao, salada e batata frita",           "32.90", "Marmitas"),
        ("Marmita - Costela Bovina",    "Costela bovina desfiada ao molho - arroz, feijao, salada e batata frita",    "32.90", "Marmitas"),
        ("Marmita - Linguica Toscana",  "Linguica toscana grelhada - arroz, feijao, salada e batata frita",           "32.90", "Marmitas"),
        ("Marmita - Tilapia Grelhada",  "File de tilapia grelhado com limao - arroz, feijao, salada e batata frita",  "32.90", "Marmitas"),
        ("Refrigerante Lata 350ml",     "Cola, guarana ou limao",                                                     "6.00",  "Bebidas"),
        ("Suco Natural 300ml",          "Laranja, maracuja ou abacaxi",                                               "9.00",  "Bebidas"),
        ("Agua Mineral 500ml",          "Com ou sem gas",                                                             "4.00",  "Bebidas"),
    ]
    for name, desc, price, cat in items_r1:
        conn.execute(text("""
            INSERT INTO menu_items (restaurant_id, name, description, price, category, is_available, created_by_id)
            VALUES (:rid, :name, :desc, :price, :cat, true, :aid)
        """), {"rid": r1, "name": name, "desc": desc, "price": price, "cat": cat, "aid": admin_id})

    print(f"OK  Restaurante 1 criado: Marmitaria Diverti (id={r1})")

    # ── Restaurant 2 ────────────────────────────────────────────────────────
    r2 = conn.execute(text("""
        INSERT INTO restaurants (event_id, name, description, is_active, created_by_id)
        VALUES (:eid, :name, :desc, true, :aid)
        RETURNING id
    """), {
        "eid": event_id,
        "name": "Cantina do Camping",
        "desc": "Comida caseira pra repor energia no camping",
        "aid": admin_id,
    }).scalar()

    items_r2 = [
        ("Marmita - Frango a Passarinho", "Pedacos de frango frito crocante - arroz, feijao, salada e batata frita",   "29.90", "Marmitas"),
        ("Marmita - Bife de Alcatra",     "Bife de alcatra grelhado com alho - arroz, feijao, salada e batata frita",  "29.90", "Marmitas"),
        ("Marmita - Carne Moida",         "Carne moida com legumes refogados - arroz, feijao, salada e batata frita",  "29.90", "Marmitas"),
        ("Marmita - Calabresa Acebolada", "Calabresa fatiada acebolada na chapa - arroz, feijao, salada e batata frita","29.90", "Marmitas"),
        ("Marmita - Ovo Estrelado Duplo", "Dois ovos estrelados na manteiga - arroz, feijao, salada e batata frita",   "24.90", "Marmitas"),
        ("Refrigerante Lata 350ml",       "Cola, guarana ou laranja",                                                  "6.00",  "Bebidas"),
        ("Suco de Polpa 300ml",           "Acai, goiaba ou caja",                                                      "10.00", "Bebidas"),
        ("Agua Mineral 500ml",            "Sem gas",                                                                   "4.00",  "Bebidas"),
        ("Isotonico 500ml",               "Repositor energetico",                                                      "8.00",  "Bebidas"),
    ]
    for name, desc, price, cat in items_r2:
        conn.execute(text("""
            INSERT INTO menu_items (restaurant_id, name, description, price, category, is_available, created_by_id)
            VALUES (:rid, :name, :desc, :price, :cat, true, :aid)
        """), {"rid": r2, "name": name, "desc": desc, "price": price, "cat": cat, "aid": admin_id})

    print(f"OK  Restaurante 2 criado: Cantina do Camping (id={r2})")

print("\nPRONTO  Seed concluido!")
print(f"  Cozinha R1: /pages/kitchen/{r1}")
print(f"  Garcom  R1: /pages/waiter/{r1}")
print(f"  Cozinha R2: /pages/kitchen/{r2}")
print(f"  Garcom  R2: /pages/waiter/{r2}")
