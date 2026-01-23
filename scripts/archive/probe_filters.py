import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("NEXUS_API_URL")
TOKEN = os.getenv("NEXUS_TOKEN")

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-API-KEY": TOKEN
}

def analyze_response(url_suffix, params_desc):
    if "?" in url_suffix and "/?" not in url_suffix:
        url_suffix = url_suffix.replace("?", "/?")
    elif "?" not in url_suffix and not url_suffix.endswith("/"):
        url_suffix += "/"
        
    url = f"{BASE_URL}/{url_suffix}"
    print(f"\n--- Testing {params_desc} ---")
    print(f"URL: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"Count: {len(data)}")
                if len(data) > 0:
                     print(f"First Date: {data[0].get('data_contrato') or data[0].get('data')}")
            elif isinstance(data, dict) and 'results' in data:
                print(f"Count: {len(data['results'])}")
                if data['results']:
                     print(f"First Date: {data['results'][0].get('data_contrato')}")
            else:
                 print("Empty or unknown format")
        else:
            print(f"Response: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

# Try standard Django filters
analyze_response("modelos?data_contrato=2025-12-12", "Filter Exact Date")
analyze_response("modelos?data=2025-12-12", "Filter Exact Data")
analyze_response("modelos?data_contrato__gte=2025-08-01", "Filter GTE Date")
analyze_response("modelos?data__gte=2025-08-01", "Filter GTE Data")
analyze_response("modelos?min_date=2025-08-01", "Filter min_date param")
analyze_response("modelos?after=2025-08-01", "Filter after param")
