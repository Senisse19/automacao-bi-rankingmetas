import os
import sys
import json

# Fix path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.services.supabase_service import SupabaseService

def inspect():
    svc = SupabaseService()
    
    print("\n--- FAZENDO INSPEÇÃO DETALHADA ---")
    
    # Unidades: Get one that is NOT named "Unidade X" if possible?
    # Or just get any and list keys.
    print("Fetching 1 Unit...")
    units = svc._get("nexus_unidades", {"limit": 1})
    if units:
        u = units[0]
        print("UNIT KEYS:", sorted(list(u.keys())))
        print("UNIT EXAMPLE:", json.dumps(u, indent=2, ensure_ascii=False))
    
    # Models: Get one
    print("\nFetching 1 Modelo...")
    models = svc._get("nexus_modelos", {"limit": 1})
    if models:
        m = models[0]
        print("MODEL KEYS:", sorted(list(m.keys())))
        print("MODEL EXAMPLE (Part):", json.dumps(m, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    inspect()
