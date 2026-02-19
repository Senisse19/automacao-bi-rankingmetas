import os
import sys
from unittest.mock import MagicMock

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

# Mock SupabaseService to avoid SharePoint env check
sys.modules["core.services.supabase_service"] = MagicMock()

from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("debug_table_direct")

INA_DATASET_ID = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
INA_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID")

client = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)


def run():
    print("--- PROBING TABLE 'Competencia' DIRECTLY ---")

    # Query 1 row from Competencia to see all columns
    query = """
    EVALUATE
    TOPN(1, 'Competencia')
    """

    print("Executing query...")
    try:
        result = client.execute_dax(query)
        if result:
            print("\n--- ROW SAMPLE ---")
            row = result[0]
            for k, v in row.items():
                print(f"Key: {k} | Value Sample: {str(v)[:50]}")
        else:
            print("No rows returned.")
    except Exception as e:
        print(f"Error executing query: {e}")


if __name__ == "__main__":
    run()
