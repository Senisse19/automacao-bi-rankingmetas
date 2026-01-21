import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def sync_modelos_only():
    client = UnidadesClient()
    svc = SupabaseService()
    
    print("\n--- Sincronizando MODELOS (DEBUG MODE) ---")
    data = client._get_paginated_latest("modelos")
    print(f"Encontrados {len(data)} modelos na API.")
    
    if not data:
        print("Nenhum dado retornado pela API.")
        return

    # Print first few items to see dates
    print("\nPrimeiros 5 itens da API:")
    for i, item in enumerate(data[:5]):
        dt = item.get("data_contrato") or item.get("data")
        print(f"{i+1}. ID: {item.get('id')} | Data: {dt}")

    batch = []
    for item in data:
        dt_contrato = item.get("data_contrato") or item.get("data")
        if dt_contrato and dt_contrato < "2024-01-01":
            continue
            
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
    
    print(f"\nModelos pendentes de insert (>= 2024): {len(batch)}")
    
    # Simple loop for reliability
    for i in range(0, len(batch), 100):
        chunk = batch[i:i + 100]
        success = svc.upsert_data("nexus_modelos", chunk)
        if success:
            print(f"Upserted items {i} to {i+len(chunk)}")
        else:
            print(f"FAILED items {i} to {i+len(chunk)}")

if __name__ == "__main__":
    sync_modelos_only()
