import requests
from config import NEXUS_CONFIG

base = NEXUS_CONFIG["api_url"]
headers = {"X-API-KEY": NEXUS_CONFIG["token"]}

endpoints = [
    "/clientes/", "/clients/", "/cliente/", "/client/",
    "/Clientes/", "/Clients/",
    "/pessoas/", "/people/"
]

print(f"Base: {base}")
for ep in endpoints:
    url = base + ep
    try:
        resp = requests.get(url, headers=headers, params={"limit": 1}, timeout=5)
        print(f"{ep} -> {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS!")
            try:
                print(resp.json())
            except:
                pass
            break
    except Exception as e:
        print(f"{ep} -> Error: {e}")
