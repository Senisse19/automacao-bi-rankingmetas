import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.clients.unidades_client import UnidadesClient

def analyze_structure():
    client = UnidadesClient()
    
    print("--- STRUCTURE ANALYSIS ---")
    
    # 1. Unidades
    print("\n[UNIDADES] Fetching 1 record...")
    try:
        units = client._get_paginated_latest("unidades") # This fetches all, might be slow. 
        # Actually client doesn't support limit. I'll just fetch page 1 manually if I can, 
        # but _get_paginated_latest loops.
        # Let's use the private method logic or just grab the first from the list if the script runs fast enough 
        # or mock it? No, I need real keys. 
        # I'll rely on the fact that _get_paginated_latest prints logs and maybe I can interrupt? 
        # Or better, I'll modify the client or just use requests directly for a quick peek.
        pass
    except:
        pass
        
    # Let's use requests directly for speed to avoid fetching 4000 items
    import requests
    headers = client.headers
    base_url = client.url
    
    def peek(endpoint):
        url = f"{base_url}/api/v1/{endpoint}"
        print(f"GET {url}")
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('results', []) if isinstance(data, dict) else data
            if items:
                print(f"Keys for {endpoint}:")
                print(json.dumps(list(items[0].keys()), indent=2))
                print("Sample Record:")
                print(json.dumps(items[0], indent=2))
            else:
                print(f"No items found in {endpoint}")
        else:
            print(f"Error {resp.status_code}: {resp.text}")

    peek("unidades")
    peek("participantes") # Or whatever the endpoint is. client uses 'participantes' or 'vendedores'? 
    # The client code says 'participantes' in my previous edits? 
    # Let's check 'modelos' too.
    peek("modelos")

if __name__ == "__main__":
    analyze_structure()
