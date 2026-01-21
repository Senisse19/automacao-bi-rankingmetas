import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def sync_unidades(client, svc):
    print("--- Sincronizando UNIDADES ---")
    data = client._get_paginated_latest("unidades")
    print(f"Encontradas {len(data)} unidades no Nexus.")
    
    batch = []
    for item in data:
        row = {
            "id": item.get("codigo"),

            "nome": item.get("nome"),
            "cidade": item.get("cidade"),
            "uf": item.get("uf"),
            "raw_data": item,
            "updated_at": datetime.now().isoformat()
        }
        batch.append(row)
    
    # Batch upsert (Supabase handles bulk inserts efficiently)
    # Split into chunks of 1000 if needed, but requests usually handles a few MBs fine.
    # Let's do chunks of 500 just to be safe.
    chunk_size = 500
    for i in range(0, len(batch), chunk_size):
        chunk = batch[i:i + chunk_size]
        success = svc.upsert_data("nexus_unidades", chunk)
        if success:
            print(f"Upserted chunk {i} - {i+len(chunk)}")
        else:
            print(f"Failed chunk {i}")

def sync_participantes(client, svc):
    print("\n--- Sincronizando PARTICIPANTES ---")
    # Using 'vendedores' or 'participantes' endpoint? UnidadesClient usually fetches 'participantes' or 'usuarios'
    # Checking UnidadesClient source, it has _get_all_participantes returning {} with a debug skip.
    # We need to fix that or use _get_paginated_latest directly on "participantes" endpoint if it exists.
    # Assuming endpoint "participantes" exists in Nexus.
    
    try:
        data = client._get_paginated_latest("participantes")
        print(f"Encontrados {len(data)} participantes no Nexus.")
        
        batch = []
        for item in data:
            row = {
                "id": item.get("id") or item.get("codigo"),

                "nome": item.get("nome"),
                "email": item.get("email"),
                "ativo": item.get("ativo", True), # Assume active if not specified
                "raw_data": item,
                "updated_at": datetime.now().isoformat()
            }
            batch.append(row)
            
        chunk_size = 500
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i:i + chunk_size]
            success = svc.upsert_data("nexus_participantes", chunk)
            if success:
                print(f"Upserted chunk {i} - {i+len(chunk)}")
            else:
                print(f"Failed chunk {i}")
    except Exception as e:
        print(f"Erro ao sync participantes: {e}")

def sync_modelos(client, svc):
    print("\n--- Sincronizando MODELOS (Vendas/Contratos) ---")
    data = client._get_paginated_latest("modelos")
    print(f"Encontrados {len(data)} modelos no Nexus.")
    
    # Pre-Fetch Known Unit IDs to avoid FK errors
    try:
        known_unit_ids = svc.get_all_ids("nexus_unidades")
        print(f"Unidades conhecidas no DB: {len(known_unit_ids)}")
    except:
        known_unit_ids = set()

    batch = []
    missing_unidade_ids = set()

    for item in data:
        # Map fields
        dt_contrato = item.get("data_contrato") or item.get("data")
        if dt_contrato == "": dt_contrato = None
        
        uid = item.get("unidade")
        
        # Filter Legacy Data (< 2024)
        if dt_contrato and dt_contrato < "2024-01-01":
            continue

        
        # Check integrity
        if uid and str(uid) not in known_unit_ids:
            missing_unidade_ids.add(str(uid))

        row = {
            "id": item.get("id") or item.get("codigo"),
            "unidade_id": uid,
            "consultor_id": item.get("consultor_venda"),
            "data_contrato": dt_contrato,
            "valor": item.get("valor") or 0,
            "status": "Cancelado" if item.get("cancelamento") == 1 else "Ativo",
            "raw_data": item,
            "updated_at": datetime.now().isoformat()
        }
        batch.append(row)
    
    # Handle Missing Units (Placeholders with real names from API)
    if missing_unidade_ids:
        print(f"⚠ Encontradas {len(missing_unidade_ids)} unidades referenciadas mas inexistentes. Buscando nomes via API...")
        placeholder_batch = []
        for miss_uid in missing_unidade_ids:
            # Try to fetch real name from Nexus API
            try:
                nome_real = client.fetch_unit_name(int(miss_uid))
            except:
                nome_real = f"Unidade {miss_uid}"
            
            placeholder_batch.append({
                "id": miss_uid,
                "nome": nome_real,
                "cidade": "-",
                "uf": "-",
                "raw_data": {"fetched_from_api": True, "original_id": miss_uid},
                "updated_at": datetime.now().isoformat()
            })
            # Add to known so we don't try to re-add? (SVC handles duplicates by upsert)
            known_unit_ids.add(miss_uid)
        
        # Insert Placeholders in chunks
        chunk_size = 500
        for i in range(0, len(placeholder_batch), chunk_size):
            chunk = placeholder_batch[i:i + chunk_size]
            svc.upsert_data("nexus_unidades", chunk)
            print(f"  -> Inserted placeholders {i} - {i+len(chunk)}")

    # Sync Models
    chunk_size = 500
    for i in range(0, len(batch), chunk_size):
        chunk = batch[i:i + chunk_size]
        success = svc.upsert_data("nexus_modelos", chunk)
        if success:
            print(f"Upserted chunk {i} - {i+len(chunk)}")
        else:
            print(f"Failed chunk {i}")

if __name__ == "__main__":
    client = UnidadesClient()
    svc = SupabaseService()
    
    sync_unidades(client, svc)
    sync_participantes(client, svc)
    sync_modelos(client, svc)
