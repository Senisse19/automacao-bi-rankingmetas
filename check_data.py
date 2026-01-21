import sys
import os
sys.path.insert(0, os.path.abspath("."))
from core.services.supabase_service import SupabaseService

def find():
    s = SupabaseService()
    try:
        # Correct column is 'data'
        res = s._get("nexus_unidades", {"select": "data", "order": "data.desc", "limit": "10"})
        if res:
            dates = [r.get('data')[:10] for r in res if r.get('data')]
            print(f"FOUND DATES: {dates}")
        else:
            print("NO DATA FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    find()
