import sys
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import UNIDADES_CONFIG

def debug_api():
    base_url = UNIDADES_CONFIG.get("api_url")
    token = UNIDADES_CONFIG.get("token")
    
    if not base_url or not token:
        print("❌ Missing Configuration (URL or Token)")
        return

    print(f"--- DEBUGGING SOURCE API: {base_url} ---")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": token
    }
    
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    tables = ["unidades", "modelos", "participantes"]
    
    # 1. Probe specific Unit
    uids = [2183, 1792, 2387]
    for uid in uids:
        print(f"\n[?] Probing Specific Unit: unidades/{uid}/ ...")
        try:
            url = f"{base_url}/unidades/{uid}/"
            resp = session.get(url, headers=headers)
            if resp.status_code == 200:
                print(f"✅ Found Unit {uid}!")
                print(json.dumps(resp.json(), indent=2, default=str))
            else:
                print(f"❌ Unit {uid} not found: {resp.status_code}")
        except Exception as e: print(e)

if __name__ == "__main__":
    debug_api()
