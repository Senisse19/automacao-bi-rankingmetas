import requests
from config import NEXUS_CONFIG

base = NEXUS_CONFIG["api_url"].replace("/api/v1", "")

# Try variations
urls = [
    base + "/Produtos/list_products_api_v1_products__get", # Pattern seen for clients
    base + "/api/v1/produtos/",
    base + "/api/v1/products/"
]
headers = {"X-API-KEY": NEXUS_CONFIG["token"]}

for url in urls:
    try:
        print(f"Testing {url}")
        resp = requests.get(url, headers=headers, params={"limit": 1}, timeout=5)
        print(resp.status_code)
        if resp.status_code == 200:
            print(resp.json())
            break
    except Exception as e:
        print(e)
