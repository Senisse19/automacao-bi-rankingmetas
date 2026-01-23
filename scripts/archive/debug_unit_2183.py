import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.supabase_service import SupabaseService

def check_unit():
    svc = SupabaseService()
    
    unit_id = 2183
    print(f"Checking Unit ID: {unit_id}")

    # Check Model Entry
    res_models = svc._get("nexus_modelos", {"unidade": f"eq.{unit_id}"})
    print(f"Models Count: {len(res_models)}")
    if res_models:
        print("Model Sample:", json.dumps(res_models[0], indent=2, default=str))

    # Check Unit Entry by ID
    res_unit_id = svc._get("nexus_unidades", {"id": f"eq.{unit_id}"})
    print(f"Unit by ID Count: {len(res_unit_id)}")
    if res_unit_id:
        print("Unit by ID:", json.dumps(res_unit_id[0], indent=2, default=str))

    # Check Unit Entry by Codigo
    res_unit_code = svc._get("nexus_unidades", {"codigo": f"eq.{unit_id}"})
    print(f"Unit by Code Count: {len(res_unit_code)}")
    if res_unit_code:
        print("Unit by Code:", json.dumps(res_unit_code[0], indent=2, default=str))

if __name__ == "__main__":
    check_unit()
