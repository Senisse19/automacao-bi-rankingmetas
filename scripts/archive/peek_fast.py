import sys
import os
import json
import requests
from dotenv import load_dotenv

# Load env from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

UNIDADES_API_URL = os.getenv("UNIDADES_API_URL")
UNIDADES_TOKEN = os.getenv("UNIDADES_TOKEN")

def peek_fast():
    if not UNIDADES_API_URL:
        print("API URL not found in env")
        return

    headers = {
        "X-API-KEY": UNIDADES_TOKEN,
        "Content-Type": "application/json"
    }
    
    endpoints = ["unidades", "participantes", "modelos"]
    
    for ep in endpoints:
        url = f"{UNIDADES_API_URL}/{ep}/"
        print(f"\n--- {ep.upper()} ---")
        try:
            resp = requests.get(url, headers=headers, params={"range": "0-1"}, timeout=10)
            if resp.status_code != 200:
                 url = f"{UNIDADES_API_URL}/{ep}"
                 resp = requests.get(url, headers=headers, params={"range": "0-1"}, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                item = None
                if isinstance(data, list) and data:
                    item = data[0]
                elif isinstance(data, dict) and "results" in data and data["results"]:
                    item = data["results"][0]
                
                if item:
                    print("Available Keys:")
                    # Print keys sorted
                    print(json.dumps(sorted(list(item.keys())), indent=2))
                    print("Sample Types:")
                    types = {k: str(type(v).__name__) for k, v in item.items()}
                    print(json.dumps(types, indent=2))
                else:
                    print("No items found.")
            else:
                print(f"Failed: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    peek_fast()
