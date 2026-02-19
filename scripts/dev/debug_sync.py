import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from core.services.supabase_service import SupabaseService
from datetime import datetime


def debug():
    print("--- DEBUG INITIALIZED ---")
    client = JobsClient()
    svc = SupabaseService()

    # 1. Testar Fetch API
    print("\n1. Testing API Fetch (Services)...")
    try:
        data = client.fetch_all("/servicos")
        print(f"API returned {len(data)} services.")
        if data:
            print(f"Sample: {data[0]}")
    except Exception as e:
        print(f"API Error: {e}")

    print("\n2. Testing API Fetch (Contracts)...")
    try:
        data = client.fetch_all("/contratos_recorrentes/")
        print(f"API returned {len(data)} contracts.")
        if data:
            print(f"Sample: {data[0]}")
    except Exception as e:
        print(f"API Error: {e}")

    # 2. Testar DB Upsert
    print("\n3. Testing DB Upsert (nexus_servicos)...")
    try:
        dummy_data = [
            {
                "codigo": 999999,
                "nome": "TESTE DEBUG",
                "sigla": "DBG",
                "modelo": 1,
                "ativo": 0,
                "updated_at": datetime.now().isoformat(),
            }
        ]
        success = svc.upsert_data("nexus_servicos", dummy_data, on_conflict="codigo")
        print(f"Upsert success: {success}")
    except Exception as e:
        print(f"DB Error: {e}")


if __name__ == "__main__":
    debug()
