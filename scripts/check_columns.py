import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.services.supabase_service import SupabaseService

def check_cols():
    svc = SupabaseService()
    print("--- CHECKING COLUMNS ---")
    
    # Try to fetch one row with *
    res = svc._get("nexus_unidades", {"limit": 1})
    if res:
        print("Keys in nexus_unidades:", list(res[0].keys()))
    else:
        print("No rows found, cannot infer columns easily via REST.")

if __name__ == "__main__":
    check_cols()
