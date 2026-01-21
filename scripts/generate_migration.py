import sys
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

UNIDADES_API_URL = os.getenv("UNIDADES_API_URL")
UNIDADES_TOKEN = os.getenv("UNIDADES_TOKEN")

TABLE_MAP = {
    "unidades": "nexus_unidades",
    "participantes": "nexus_participantes",
    "modelos": "nexus_modelos"
}

def infer_type(key, value):
    if key == "id" or key == "codigo":
        return None # Skip primary keys, already exist
    
    if "data" in key or "_at" in key:
        return "timestamp with time zone"
        
    if isinstance(value, int):
        return "bigint"
    if isinstance(value, float):
        return "numeric"
    if isinstance(value, bool):
        return "boolean"
    return "text"

def generate_sql():
    if not UNIDADES_API_URL:
        print("Error: No API URL")
        return

    headers = {
        "X-API-KEY": UNIDADES_TOKEN,
        "Content-Type": "application/json"
    }
    
    endpoints = ["unidades", "participantes", "modelos"]
    
    print("-- AUTO-GENERATED MIGRATION --")
    
    for ep in endpoints:
        table_name = TABLE_MAP.get(ep)
        url = f"{UNIDADES_API_URL}/{ep}/"
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
                    print(f"\n-- {table_name} ({ep})")
                    for key, value in sorted(item.items()):
                        pg_type = infer_type(key, value)
                        if pg_type:
                            print(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS \"{key}\" {pg_type};")
            else:
                print(f"-- Failed to fetch {ep}: {resp.status_code}")
        except Exception as e:
            print(f"-- Error fetching {ep}: {e}")

if __name__ == "__main__":
    # Redirect output to file manually to ensure encoding
    import io
    
    # buffer the output
    output = []
    def my_print(s):
        output.append(s)
        
    # Monkey patch print? No, let's just change the function logic to return string or write to file
    # Re-defining generate_sql to write to file
    pass

def generate_sql_to_file():
    if not UNIDADES_API_URL:
        print("Error: No API URL")
        return

    headers = {
        "X-API-KEY": UNIDADES_TOKEN,
        "Content-Type": "application/json"
    }
    
    endpoints = ["unidades", "participantes", "modelos"]
    
    with open("migration_fixed.sql", "w", encoding="utf-8") as f:
        f.write("-- AUTO-GENERATED MIGRATION --\n")
        
        for ep in endpoints:
            table_name = TABLE_MAP.get(ep)
            url = f"{UNIDADES_API_URL}/{ep}/"
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
                        f.write(f"\n-- {table_name} ({ep})\n")
                        for key, value in sorted(item.items()):
                            pg_type = infer_type(key, value)
                            if pg_type:
                                # Quote column names to handle reserved words or clean them
                                clean_key = key.replace(" ", "_")
                                f.write(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS \"{clean_key}\" {pg_type};\n")
                else:
                     f.write(f"-- Failed to fetch {ep}: {resp.status_code}\n")
            except Exception as e:
                 f.write(f"-- Error fetching {ep}: {e}\n")
    print("Migration file generated: migration_fixed.sql")

if __name__ == "__main__":
    generate_sql_to_file()
