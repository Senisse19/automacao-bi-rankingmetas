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
    
    print("\n--- SYSTEM SETTINGS: MODEL MAP ---")
    m_map = svc.get_setting("nexus_model_map")
    print(json.dumps(m_map, indent=2, ensure_ascii=False))
    
    print("\n--- NEXUS_UNIDADES (1 ROW) ---")
    data = svc._get("nexus_unidades", {"limit": 1, "order": "id.desc", "select": "*"})
    if data:
        print(json.dumps(data[0], indent=2, ensure_ascii=False))
        
    print("\n--- NEXUS_MODELOS (1 ROW) ---")
    data = svc._get("nexus_modelos", {"limit": 1, "order": "id.desc", "select": "*"})
    if data:
        print(json.dumps(data[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    inspect()
