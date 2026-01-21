import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NEXUS_API_URL")
TOKEN = os.getenv("NEXUS_TOKEN")

headers = {
    "X-API-KEY": TOKEN,
    "Content-Type": "application/json"
}

def probe():
    url = f"{BASE_URL}/modelos/"
    print(f"URL: {url}")
    print(f"Token (First 8): {TOKEN[:8]}...")
    
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    data = resp.json()
    if isinstance(data, dict):
        items = data.get("results", [])
    else:
        items = data
    
    print(f"Total Items in Response: {len(items)}")

    
    if items:
        first = items[0]
        last = items[-1]
        print(f"\n--- PAGINA 1 ---")
        print(f"Primeiro item (ID: {first.get('id')}): Data {first.get('data')} | Contrato {first.get('data_contrato')}")
        print(f"Último item (ID: {last.get('id')}): Data {last.get('data')} | Contrato {last.get('data_contrato')}")
        
    # Check if there is 2026 data at all by filtering
    print("\n--- TESTANDO FILTRO 2026 ---")
    url_2026 = f"{url}?data_contrato__gte=2026-01-01"
    resp_2026 = requests.get(url_2026, headers=headers)
    items_2026 = resp_2026.json().get("results", [])
    print(f"Items >= 2026-01-01: {len(items_2026)}")
    if items_2026:
        print(f"Primeiro item 2026: {items_2026[0].get('data_contrato')}")

if __name__ == "__main__":
    probe()
