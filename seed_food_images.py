"""
Adds image_urls to restaurants and menu items.
  cd back
  python seed_food_images.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.config.admin_db import admin_engine
from sqlalchemy import text

U = "https://images.unsplash.com/photo-"
Q = "?auto=format&fit=crop&w=800&q=80"
def img(id): return f"{U}{id}{Q}"

RESTAURANT_IMAGES = {
    "Marmitaria Diverti": img("1555396273-367ea4eb4db5"),   # colorful food counter
    "Cantina do Camping":  img("1414235077428-338989a2e8c0"), # cozy restaurant table
}

ITEM_IMAGES = {
    # marmitas R1
    "Marmita - Frango Grelhado":   img("1532550907401-a500c9a57435"),  # grilled chicken
    "Marmita - Picanha":           img("1546833998-877b37c2e5c6"),     # steak on grill
    "Marmita - Costela Bovina":    img("1544025162-d76694265947"),     # beef ribs
    "Marmita - Linguica Toscana":  img("1555939594-58d7cb561ad1"),     # grilled sausage
    "Marmita - Tilapia Grelhada":  img("1519708227418-c8fd9a32b7a2"),  # grilled fish
    # marmitas R2
    "Marmita - Frango a Passarinho": img("1562802378-063ec186a863"),   # fried chicken pieces
    "Marmita - Bife de Alcatra":     img("1558030006-450675393462"),   # steak plate
    "Marmita - Carne Moida":         img("1568901346375-23c9450c58cd"), # ground beef
    "Marmita - Calabresa Acebolada": img("1627308595229-7830a5c91f9f"), # sausage sliced
    "Marmita - Ovo Estrelado Duplo": img("1612487528505-d2338264c821"), # fried eggs
    # bebidas (shared)
    "Refrigerante Lata 350ml": img("1581636625402-29b2a704ef13"),  # soda can
    "Suco Natural 300ml":      img("1621506289937-a8e4df240d0b"),  # orange juice glass
    "Agua Mineral 500ml":      img("1548839140-29a749e1cf4d"),     # water bottle
    "Suco de Polpa 300ml":     img("1600271886742-f049cd451bba"),  # fruit smoothie
    "Isotonico 500ml":         img("1594128655685-de62e3ff617c"),  # sports drink
}

with admin_engine.begin() as conn:
    # restaurants
    for name, url in RESTAURANT_IMAGES.items():
        res = conn.execute(text(
            "UPDATE restaurants SET image_url=:url WHERE name=:name AND deleted_at IS NULL"
        ), {"url": url, "name": name})
        print(f"  restaurante '{name}': {res.rowcount} linha(s)")

    # menu items
    for name, url in ITEM_IMAGES.items():
        res = conn.execute(text(
            "UPDATE menu_items SET image_url=:url WHERE name=:name AND deleted_at IS NULL"
        ), {"url": url, "name": name})
        print(f"  item '{name}': {res.rowcount} linha(s)")

print("\nPRONTO  Imagens atualizadas!")
