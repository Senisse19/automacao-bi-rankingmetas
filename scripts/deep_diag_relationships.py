import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.services.supabase_service import SupabaseService

def deep_diag():
    svc = SupabaseService()
    print("--- DEEP DIAG START ---")
    
    # 1. Get Samples
    print("\n[1] Fetching Sample Modelos...")
    res_models = svc._get("nexus_modelos", {"limit": 20, "order": "updated_at.desc"})
    if not res_models:
        print("No models found!")
        return
        
    sample_ids = set()
    for m in res_models:
        uid = m.get("unidade_id") or m.get("unidade")
        print(f"Model {m.get('id')}: unidade_id={uid}")
        if uid:
            sample_ids.add(str(uid))
            
    # 2. Check Existence
    print(f"\n[2] Checking {len(sample_ids)} IDs in nexus_unidades...")
    if not sample_ids:
        print("No unit IDs to check.")
    else:
        ids_str = ",".join(sample_ids)
        res_units = svc._get("nexus_unidades", {"id": f"in.({ids_str})"})
        found_ids = {str(u['id']) for u in res_units} if res_units else set()
        
        print(f"Found {len(found_ids)} matches out of {len(sample_ids)} checked.")
        print(f"Missing: {sample_ids - found_ids}")
        
    # 3. Test JOIN syntax
    print("\n[3] Testing Join Syntax...")
    
    # Try 1: Unaliased using Table Name
    # If the FK is on unidade_id, and points to nexus_unidades.id
    # PostgREST usually detects it.
    
    print("Trying: select=id,nexus_unidades!inner(id)")
    r1 = svc._get("nexus_modelos", {"select": "id,nexus_unidades!inner(id)", "limit": 1})
    print(f"Result 1 (Table Name): {r1}")
    
    print("Trying: select=id,unidade:nexus_unidades!inner(id)")
    r2 = svc._get("nexus_modelos", {"select": "id,unidade:nexus_unidades!inner(id)", "limit": 1})
    print(f"Result 2 (Aliased): {r2}")
    
    # Try using column name hint if ambiguous
    print("Trying: select=id,nexus_unidades!unidade_id!inner(id)")
    r3 = svc._get("nexus_modelos", {"select": "id,nexus_unidades!unidade_id!inner(id)", "limit": 1})
    print(f"Result 3 (FK Hint): {r3}")

if __name__ == "__main__":
    deep_diag()
