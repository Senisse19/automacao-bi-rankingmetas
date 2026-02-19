import sys
import os
from dotenv import load_dotenv

# Load env vars from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

try:
    from core.clients.powerbi_client import PowerBIClient
except ImportError:
    # Handle if run from outside the module
    # Added: resolve project root relative to this script (scripts/dev/find_ina.py -> ../../)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    if project_root not in sys.path:
        sys.path.append(project_root)

    from core.clients.powerbi_client import PowerBIClient

print("--- SEARCHING FOR DATASET 'painel_ina' ---")

try:
    client = PowerBIClient()
    if client.authenticate():
        datasets = client.list_datasets()
        found = False
        for ds in datasets:
            name = ds.get("name", "")
            if "ina" in name.lower():
                print(f"✅ FOUND: '{name}' (ID: {ds['id']})")
                found = True

        if not found:
            print("❌ NOT FOUND matching 'ina'.")
            print("Available datasets (first 10):")
            for ds in datasets[:10]:
                print(f"- {ds.get('name')}")
    else:
        print("❌ Authentication Failed.")

except Exception as e:
    print(f"❌ Error: {e}")
