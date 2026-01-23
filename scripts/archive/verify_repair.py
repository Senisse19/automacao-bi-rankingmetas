import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.services.supabase_service import SupabaseService

def verify():
    svc = SupabaseService()
    print("--- VERIFYING REPAIR ---")
    
    ids_to_check = [1792, 2387, 2183]
    for uid in ids_to_check:
        res = svc._get("nexus_unidades", {"id": f"eq.{uid}"})
        if res:
            print(f"✅ Unit {uid}: Found! Name='{res[0].get('nome')}'")
        else:
            print(f"❌ Unit {uid}: NOT FOUND in Supabase.")

    print("\n--- TEST COUNT QUERY AGAIN ---")
    # Same as page.tsx qNew
    # select count, unidade:nexus_unidades!inner(id)
    # status=Ativo
    params = {
        "select": "id, unidade:nexus_unidades!inner(id)",
        "status": "eq.Ativo",
        "limit": 5
    }
    res = svc._get("nexus_modelos", params)
    print(f"Query returned {len(res)} valid joined rows.")
    if res:
        print("Sample:", json.dumps(res[0], indent=2, default=str))

if __name__ == "__main__":
    verify()
