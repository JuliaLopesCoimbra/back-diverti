"""
Script de migração para copiar dados da tabela prizes do banco local para o online
Execute este script para migrar todos os prêmios do banco db_roulette local para o banco online

Uso:
    python app\infra\script\insert_prizes.py
    (execute a partir do diretório back-n1)
"""

import sys
from pathlib import Path

# Adicionar o diretório back-n1 ao PYTHONPATH
script_dir = Path(__file__).resolve().parent
back_n1_dir = script_dir.parent.parent.parent  # Volta de script -> infra -> app -> back-n1
sys.path.insert(0, str(back_n1_dir))

from sqlalchemy import create_engine, text
from app.config.settings import settings

# URL do banco local - AJUSTE ESTA URL CONFORME SEU AMBIENTE LOCAL
LOCAL_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/db_roulette"

# URL do banco online (vem das variáveis de ambiente)
ONLINE_DATABASE_URL = settings.ROULETTE_DATABASE_URL


def migrate_prizes():
    """Migra todos os dados da tabela prizes do banco local para o online"""
    
    # Criar engines para ambos os bancos
    local_engine = create_engine(LOCAL_DATABASE_URL, echo=False)
    online_engine = create_engine(ONLINE_DATABASE_URL, echo=False)
    
    print("=" * 60)
    print("Migração de Prizes: Local → Online")
    print("=" * 60)
    print()
    
    try:
        # Conectar ao banco local e ler todos os prizes
        print("📖 Lendo dados do banco local...")
        with local_engine.connect() as local_conn:
            result = local_conn.execute(text("SELECT id, event_id, name, probability, position, image_url, is_active FROM prizes"))
            prizes_local = result.fetchall()
            
            if not prizes_local:
                print("⚠️  Nenhum prêmio encontrado no banco local.")
                return
            
            print(f"✅ Encontrados {len(prizes_local)} prêmios no banco local")
            print()
        
        # Conectar ao banco online e inserir os dados
        print("📝 Inserindo dados no banco online...")
        with online_engine.begin() as online_conn:  # begin() cria uma transação
            inserted = 0
            skipped = 0
            errors = 0
            
            for prize_row in prizes_local:
                try:
                    # Acessar os dados da tupla/row
                    prize_id = prize_row[0]
                    event_id = prize_row[1]
                    name = prize_row[2]
                    probability = prize_row[3]
                    position = prize_row[4]
                    image_url = prize_row[5]
                    is_active = prize_row[6]
                    
                    # Verificar se já existe (por event_id e position)
                    check_query = text("""
                        SELECT id FROM prizes 
                        WHERE event_id = :event_id AND position = :position
                    """)
                    existing = online_conn.execute(
                        check_query, 
                        {"event_id": event_id, "position": position}
                    ).fetchone()
                    
                    if existing:
                        print(f"   ⏭️  Prêmio '{name}' (event_id={event_id}, position={position}) já existe. Pulando...")
                        skipped += 1
                        continue
                    
                    # Inserir o prêmio
                    insert_query = text("""
                        INSERT INTO prizes (id, event_id, name, probability, position, image_url, is_active)
                        VALUES (:id, :event_id, :name, :probability, :position, :image_url, :is_active)
                    """)
                    
                    online_conn.execute(insert_query, {
                        "id": prize_id,
                        "event_id": event_id,
                        "name": name,
                        "probability": probability,
                        "position": position,
                        "image_url": image_url,
                        "is_active": is_active
                    })
                    
                    inserted += 1
                    print(f"   ✅ Inserido: '{name}' (ID: {prize_id})")
                    
                except Exception as e:
                    errors += 1
                    print(f"   ❌ Erro ao inserir prêmio ID {prize_id}: {e}")
            
            print()
            print("=" * 60)
            print("📊 Resumo da Migração:")
            print("=" * 60)
            print(f"   ✅ Inseridos: {inserted}")
            print(f"   ⏭️  Pulados (já existem): {skipped}")
            print(f"   ❌ Erros: {errors}")
            print(f"   📦 Total processado: {len(prizes_local)}")
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        raise
    finally:
        local_engine.dispose()
        online_engine.dispose()


if __name__ == "__main__":
    print()
    print("⚠️  ATENÇÃO: Certifique-se de que:")
    print("   1. A URL do banco local está correta no script")
    print("   2. A variável ROULETTE_DATABASE_URL está configurada para o banco online")
    print("   3. Você tem permissão de escrita no banco online")
    print()
    
    resposta = input("Deseja continuar? (s/n): ")
    if resposta.lower() != 's':
        print("Migração cancelada.")
        exit()
    
    print()
    migrate_prizes()
    print()
    print("✅ Migração finalizada!")
    print()