import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.supabase_service import SupabaseService

def diagnose():
    svc = SupabaseService()
def diagnose():
    svc = SupabaseService()
    print("--- SIMPLE CHECK ---")
    
    # Check ID 2183
    res = svc._get("nexus_unidades", {"id": "eq.2183"})
    if res:
        print("✅ Unit 2183 Found in Supabase!")
        print(json.dumps(res[0], indent=2, default=str))
    else:
        print("❌ Unit 2183 NOT FOUND in Supabase.")
        
    res_1 = svc._get("nexus_unidades", {"id": "eq.1"})
    print(f"Unit 1: {res_1[0].get('nome') if res_1 else 'Not Found'}")

if __name__ == "__main__":
    diagnose()
