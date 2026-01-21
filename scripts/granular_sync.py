import sys
import os
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def granular_sync():
    client = UnidadesClient()
    svc = SupabaseService()
    
    # Fetch all models
    all_modelos = client._get_paginated_latest("modelos")
    valid_modelos = [m for m in all_modelos if (m.get("data_contrato") or m.get("data") or "") >= "2024-01-01"]
    
    print(f"Total valid models (2024+): {len(valid_modelos)}")
    
    failed_count = 0
    success_count = 0
    
    for m in valid_modelos:
        dt = m.get("data_contrato") or m.get("data")
        row = {
            "id": m.get("id") or m.get("codigo"),
            "unidade_id": m.get("unidade"),
            "consultor_id": m.get("consultor_venda"),
            "data_contrato": dt,
            "valor": m.get("valor") or 0,
            "status": "Cancelado" if m.get("cancelamento") == 1 else "Ativo",
            "raw_data": m,
            "updated_at": datetime.now().isoformat()
        }
        
        url = f"{svc.url}/rest/v1/nexus_modelos?on_conflict=id"
        headers = svc.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        
        resp = requests.post(url, headers=headers, json=row)
        if resp.status_code in [200, 201, 204]:
            success_count += 1
        else:
            failed_count += 1
            print(f"FAILED model {row['id']} (Unit {row['unidade_id']}): {resp.status_code} - {resp.text}")
            
    print(f"Done. Success: {success_count}, Failed: {failed_count}")

if __name__ == "__main__":
    granular_sync()
