import sys
import os
import requests
sys.path.insert(0, os.path.abspath("."))
from core.services.supabase_service import SupabaseService

def diagnose():
    s = SupabaseService()
    print(f"URL: {s.url}")
    print(f"Key loaded: {'Yes' if s.key else 'No'}")
    
    # 1. Check a known table (automation_schedules)
    print("\n--- Testing automation_schedules ---")
    try:
        res = s._get("automation_schedules", {"limit": "1"})
        print(f"Success. Found: {len(res)} items")
    except Exception as e:
        print(f"Failed: {e}")

    # 2. Check nexus_unidades with NO params
    print("\n--- Testing nexus_unidades (No Params) ---")
    try:
        # Intentionally no params to avoid syntax errors
        res = s._get("nexus_unidades", {}) 
        print(f"Success. Found: {len(res)} items")
        if res:
            first = res[0]
            import json
            print("FULL RECORD:")
            print(json.dumps(first, indent=2, default=str))
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    diagnose()
