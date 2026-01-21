import sys
import os
import requests
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def debug_one():
    client = UnidadesClient()
    svc = SupabaseService()
    
    # Fetch models
    modelos = client._get_paginated_latest("modelos")
    target_model = None
    for m in modelos:
        if str(m.get("unidade")) == "503117":
            target_model = m
            break
            
    if not target_model:
        print("Target model for unit 503117 not found in API.")
        return
        
    print(f"Testing model ID {target_model.get('id')} with unit {target_model.get('unidade')}")
    
    # Prepare row
    dt = target_model.get("data_contrato") or target_model.get("data")
    row = {
        "id": target_model.get("id"),
        "unidade_id": target_model.get("unidade"),
        "consultor_id": target_model.get("consultor_venda"),
        "data_contrato": dt,
        "valor": target_model.get("valor") or 0,
        "status": "Cancelado" if target_model.get("cancelamento") == 1 else "Ativo",
        "raw_data": target_model,
        "updated_at": datetime.now().isoformat()
    }
    
    # Manual Request to see full error
    url = f"{svc.url}/rest/v1/nexus_modelos?on_conflict=id"
    headers = svc.headers.copy()
    headers["Prefer"] = "resolution=merge-duplicates"
    
    resp = requests.post(url, headers=headers, json=row)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    debug_one()
