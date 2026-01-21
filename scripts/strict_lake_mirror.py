import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def robust_fetch(client, endpoint):
    """Fetch all pages with multiple retries on timeout."""
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client._get_paginated_latest(endpoint)
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠ Erro ao buscar {endpoint} (tentativa {attempt+1}): {e}. Tentando novamente em 5s...")
                time.sleep(5)
            else:
                print(f"❌ Falha fatal ao buscar {endpoint} após {max_retries} tentativas: {e}")
                raise

def strict_mirror():
    client = UnidadesClient()
    svc = SupabaseService()
    
    print("\n--- INICIANDO ESPELHAMENTO ESTRITO (DATA LAKE -> SUPABASE) ---")
    
    # 1. Sync Unidades (Strictly 1:1)
    print("\n[1/3] Sincronizando Unidades...")
    unidades_data = robust_fetch(client, "unidades")
    print(f"Encontradas {len(unidades_data)} unidades na API.")
    
    unidades_batch = []
    for item in unidades_data:
        # Base mapping
        record = {
            "id": item.get("codigo"),
            "nome": item.get("nome"),
            "cidade": item.get("cidade"),
            "uf": item.get("uf"),
            # raw_data removed
            "updated_at": datetime.now().isoformat()
        }
        # Dynamic mapping for all other fields
        for k, v in item.items():
            if k not in ["codigo"]: 
                clean_k = k.replace(" ", "_")
                record[clean_k] = v
        unidades_batch.append(record)
    
    print(f"Fazendo upsert de {len(unidades_batch)} unidades...")
    for i in range(0, len(unidades_batch), 500):
        chunk = unidades_batch[i:i+500]
        svc.upsert_data("nexus_unidades", chunk)

    # 2. Sync Participantes (Strictly 1:1)
    print("\n[2/3] Sincronizando Participantes...")
    participantes_data = robust_fetch(client, "participantes")
    print(f"Encontrados {len(participantes_data)} participantes na API.")
    
    participantes_batch = []
    for item in participantes_data:
        record = {
            "id": item.get("id") or item.get("codigo"),
            "nome": item.get("nome"),
            "email": item.get("email"),
            "ativo": item.get("ativo", True),
            # raw_data removed
            "updated_at": datetime.now().isoformat()
        }
        for k, v in item.items():
             if k not in ["id", "codigo"]:
                clean_k = k.replace(" ", "_")
                record[clean_k] = v
        participantes_batch.append(record)
        
    print(f"Fazendo upsert de {len(participantes_batch)} participantes...")
    for i in range(0, len(participantes_batch), 500):
        chunk = participantes_batch[i:i+500]
        svc.upsert_data("nexus_participantes", chunk)

    # 3. Sync Modelos (Strictly 1:1)
    print("\n[3/3] Sincronizando Modelos (Vendas/Contratos)...")
    modelos_data = robust_fetch(client, "modelos")
    print(f"Encontrados {len(modelos_data)} modelos na API.")
    
    modelos_batch = []
    for item in modelos_data:
        dt = item.get("data_contrato") or item.get("data")
        # Sync ALL models, no date filter
        if True:
            record = {
                "id": item.get("id") or item.get("codigo"),
                "unidade_id": item.get("unidade"),
                "consultor_id": item.get("consultor_venda"),
                "data_contrato": dt,
                "valor": item.get("valor") or 0,
                "status": "Cancelado" if item.get("cancelamento") == 1 else "Ativo",
                # raw_data removed
                "updated_at": datetime.now().isoformat()
            }
            for k, v in item.items():
                if k not in ["id", "codigo"]:
                    clean_k = k.replace(" ", "_")
                    record[clean_k] = v
            modelos_batch.append(record)
            
    print(f"Fazendo upsert de {len(modelos_batch)} modelos (2024+)...")
    for i in range(0, len(modelos_batch), 200):
        chunk = modelos_batch[i:i+200]
        svc.upsert_data("nexus_modelos", chunk)
    
    print("\n--- ESPELHAMENTO FINALIZADO COM SUCESSO ---")

if __name__ == "__main__":
    strict_mirror()
