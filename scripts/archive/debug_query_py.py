import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.supabase_service import SupabaseService

def debug_query():
    svc = SupabaseService()
    print("--- MODEL DUMP ---")
    res = svc._get("nexus_modelos", {"limit": 1, "order": "updated_at.desc"})
    if res:
        print(json.dumps(res[0], indent=2, default=str))
    else:
        print("No models found.")


    print("\n[2] Testing LEFT JOIN...")
    params_data = {
        "select": "id, unidade_id, unidade:nexus_unidades(id, nome)",
        "limit": 5,
        "offset": 0,
        "order": "updated_at.desc",
        "status": "eq.Ativo"
    }

    print(f"GET params: {params_data}")
    res_data = svc._get("nexus_modelos", params_data)
    
    if hasattr(res_data, 'status_code'): # Check for error
         print("Error?", res_data)
    
    if isinstance(res_data, list):
         print(f"✅ Data Query Success. Returned {len(res_data)} rows.")
         if len(res_data) > 0:
             print("Sample Row 0:", json.dumps(res_data[0], indent=2, default=str))
         else:
             print("⚠ Returned 0 rows! Why?")
    else:
        print("❌ Error Response:", res_data)

    # 3. Test Join on Consultor separately
    print("\n[3] Testing Join on Consultor...")
    params_cons = {
        "select": "id, consultor:nexus_participantes(*)",
        "limit": 1
    }
    res_cons = svc._get("nexus_modelos", params_cons)
    if isinstance(res_cons, list) and len(res_cons) > 0:
         print(f"Consultor Join OK: {res_cons[0]}")
    else:
         print(f"Consultor Join Failed: {res_cons}")

if __name__ == "__main__":
    debug_query()
