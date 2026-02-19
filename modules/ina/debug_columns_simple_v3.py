import os
import sys
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Load env
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
load_dotenv(os.path.join(project_root, ".env"))

sys.path.append(project_root)

# Mock SupabaseService to avoid SharePoint env check
sys.modules["core.services.supabase_service"] = MagicMock()

from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("debug_simple_v3")

INA_DATASET_ID = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
INA_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID")

client = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)


def run():
    print("--- PROBING COLUMNS IN 'Competencia' ---")

    # Check for likely name columns
    q_cols = """
    SELECT [Name] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND ([Name] LIKE '%nome%' OR [Name] LIKE '%fantasia%' OR [Name] LIKE '%razao%')
    """
    try:
        res = client.execute_dax(q_cols)
        print("Possible Name Columns:", res)
    except Exception as e:
        print(f"Error cols: {e}")

    # Check distinct values for 'nome_fantasia'
    print("\n--- CHECKING VALUES FOR 'nome_fantasia' ---")
    try:
        res_vals = client.execute_dax("EVALUATE TOPN(5, VALUES('Competencia'[nome_fantasia]))")
        print("Values (nome_fantasia):", res_vals)
    except:
        print("Could not query nome_fantasia")

    # Check for 'Dias' related columns to fix the 270 days issue
    print("\n--- CHECKING 'Dias' COLUMNS ---")
    q_days = """
    SELECT [Name] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND ([Name] LIKE '%Dias%' OR [Name] LIKE '%Atraso%')
    """
    try:
        res_days = client.execute_dax(q_days)
        print("Possible Days Columns (Raw):", res_days)
    except:
        pass

    # Check for MEASURES
    print("\n--- CHECKING MEASURES ---")
    q_measures = """
    SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND ([Name] LIKE '%Dias%' OR [Name] LIKE '%Atraso%')
    """
    try:
        res_measures = client.execute_dax(q_measures)
        print("Possible Days Measures:", res_measures)
    except:
        pass


if __name__ == "__main__":
    run()
