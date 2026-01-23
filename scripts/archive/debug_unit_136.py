import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.services.supabase_service import SupabaseService

def debug_136():
    svc = SupabaseService()
    print("--- DEBUG UNIT 136 ---")
    
    # 1. Check Unidade
    print("\n[1] Checking nexus_unidades ID 136...")
    res_u = svc._get("nexus_unidades", {"id": "eq.136"})
    if res_u:
        print("✅ Found Unit 136 in DB:")
        print(json.dumps(res_u[0], indent=2, default=str))
    else:
        print("❌ Unit 136 NOT FOUND in DB.")

    # 2. Check Modelos
    print("\n[2] Checking nexus_modelos for unidade_id 136...")
    res_m = svc._get("nexus_modelos", {"unidade_id": "eq.136", "limit": 5})
    if res_m:
        print(f"✅ Found {len(res_m)} models.")
        print("Sample Model:", json.dumps(res_m[0], indent=2, default=str))
    else:
        print("❌ No models for Unit 136.")
        
    # 3. Check Consultor (if model exists)
    if res_m:
        cid = res_m[0].get("consultor_id")
        print(f"\n[3] Checking Consultor ID {cid}...")
        if cid:
            res_c = svc._get("nexus_participantes", {"id": f"eq.{cid}"})
            if res_c:
                print("✅ Found Consultor:")
                print(json.dumps(res_c[0], indent=2, default=str))
            else:
                print("❌ Consultor NOT FOUND.")
        else:
            print("⚠ Model has no consultor_id.")

if __name__ == "__main__":
    debug_136()
