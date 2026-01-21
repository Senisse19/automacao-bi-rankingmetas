import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

def diag():
    client = UnidadesClient()
    svc = SupabaseService()
    
    # Check 503117 specifically
    target = "503117"
    
    existing = svc.get_all_ids("nexus_unidades")
    print(f"Target {target} in existing? {target in existing}")
    print(f"Total existing: {len(existing)}")
    
    # Check if any ID looks like 503117 but different type?
    # get_all_ids converts everything to str.
    
    # Let's fetch the first 100 modèles and check their units
    modelos = client._get_paginated_latest("modelos")
    found = False
    for m in modelos:
        uid = str(m.get("unidade"))
        if uid == target:
            print(f"Found model referencing {target}! Data: {m.get('data_contrato')}")
            found = True
            break
    if not found:
        print(f"Unit {target} NOT FOUND in first page of models (or whatever was fetched).")

if __name__ == "__main__":
    diag()
