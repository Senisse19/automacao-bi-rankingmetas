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
    # This might be heavy
    data = client._get_paginated_latest("modelos")
    print(f"Encontrados {len(data)} modelos no Nexus.")
    
    batch = []
    for item in data:
        # Map fields
        # Check if dates are empty strings
        dt_contrato = item.get("data_contrato") or item.get("data")
        if dt_contrato == "": dt_contrato = None
        
        row = {
            "id": item.get("id") or item.get("codigo"),
            "unidade_id": item.get("unidade"),
            "consultor_id": item.get("consultor_venda"),
            "data_contrato": dt_contrato,
            "valor": item.get("valor") or 0,
            "status": "Cancelado" if item.get("cancelamento") == 1 else "Ativo",
            "raw_data": item,
            "updated_at": datetime.now().isoformat()
        }
        batch.append(row)
        
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
