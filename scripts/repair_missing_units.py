import sys
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.supabase_service import SupabaseService
from config import UNIDADES_CONFIG

def repair():
    svc = SupabaseService()
    print("--- REPAIR MISSING UNITS ---")
    
    # 1. Find Missing IDs
    print("[1] Identifying missing Unit IDs...")
    
    # Fetch all Model Unit IDs (distinct)
    # Using SQL if possible or fetch all (pagination)
    # Fetching 10k models might be heavy but we need distinct units.
    # Supabase unique? .select('unidade_id')
    
    # Let's fetch chunks of models and gather IDs
    model_unit_ids = set()
    offset = 0
    while True:
        res = svc._get("nexus_modelos", {"select": "unidade_id", "offset": offset, "limit": 1000})
        if not res: break
        for r in res:
             uid = r.get("unidade_id")
             if uid: model_unit_ids.add(str(uid))
        if len(res) < 1000: break
        offset += 1000
        print(f"Scanned {offset} models...")
        
    print(f"Total Unique Unit IDs in Models: {len(model_unit_ids)}")
    
    # Fetch Existing Units
    existing_ids = set()
    offset = 0
    while True:
        res = svc._get("nexus_unidades", {"select": "id", "offset": offset, "limit": 1000})
        if not res: break
        for r in res:
            existing_ids.add(str(r['id']))
        if len(res) < 1000: break
        offset += 1000
        
    print(f"Total Existing Units: {len(existing_ids)}")
    
    missing = model_unit_ids - existing_ids
    print(f"⚠ Missing Units: {len(missing)}")
    if not missing:
        print("✅ No missing units found.")
        return

    print(f"Missing Sample: {list(missing)[:10]}")
    
    # 2. Fetch from Source API
    print("\n[2] Fetching Missing from Source API...")
    
    base_url = UNIDADES_CONFIG.get("api_url")
    token = UNIDADES_CONFIG.get("token")
    headers = {"Content-Type": "application/json", "X-API-KEY": token}
    
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    
    repaired_batch = []
    
    for i, uid in enumerate(missing):
        try:
            url = f"{base_url}/unidades/{uid}/"
            resp = session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Prepare record
                record = {
                    "id": data.get("codigo"),
                    "nome": data.get("nome"),
                    "cidade": data.get("cidade"),
                    "uf": data.get("uf"),
                    "updated_at": "2026-01-23T12:00:00"
                }
                # Dynamic fields
                for k,v in data.items():
                    if k not in ["codigo"]:
                         clean_k = k.replace(" ", "_")
                         record[clean_k] = v
                
                repaired_batch.append(record)
                print(f"  + Retrieved {uid}")
            else:
                print(f"  ❌ Failed to retrieve {uid}: {resp.status_code}")
                # Create Placeholder?
                # If we don't create placeholder, !inner will still hide it.
                # Better create placeholder if 404.
                repaired_batch.append({
                    "id": uid,
                    "nome": f"Unidade {uid} (N/A)",
                    "cidade": "-",
                    "uf": "-",
                    "updated_at": "2026-01-23T12:00:00"
                })
        except Exception as e:
            print(f"  ⚠ Exception {uid}: {e}")
            
        if len(repaired_batch) >= 100:
             svc.upsert_data("nexus_unidades", repaired_batch)
             repaired_batch = []
             print("  >> Flushed batch")
             
    if repaired_batch:
        svc.upsert_data("nexus_unidades", repaired_batch)
        print("  >> Flushed final batch")

if __name__ == "__main__":
    repair()
