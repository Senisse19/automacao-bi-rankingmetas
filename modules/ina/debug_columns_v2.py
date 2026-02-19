import os
import sys
from dotenv import load_dotenv

# Load env before anything else
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
load_dotenv(os.path.join(project_root, ".env"))

# Set dummy env vars for SharePoint/Supabase to bypass validation
os.environ["SHAREPOINT_TENANT"] = "dummy"
os.environ["SHAREPOINT_CLIENT_ID"] = "dummy"
os.environ["SHAREPOINT_CLIENT_SECRET"] = "dummy"
os.environ["SUPABASE_URL"] = "https://dummy.supabase.co"
os.environ["SUPABASE_KEY"] = "dummy"

sys.path.append(project_root)

from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("debug_isolated_v2")

INA_DATASET_ID = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
INA_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID")

client = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)


def run():
    print("--- PROBING COLUMNS IN 'Competencia' ---")

    # Check for likely name columns
    q_cols = """
    SELECT [Name] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND ([Name] LIKE '%nome%' OR [Name] LIKE '%cliente%' OR [Name] LIKE '%razao%')
    """
    try:
        res = client.execute_dax(q_cols)
        print("Possible Name Columns:", res)
    except Exception as e:
        print(f"Error cols: {e}")

    # Check distinct values for 'nome_fantasia' vs 'nome' if exists
    print("\n--- CHECKING VALUES FOR 'nome_fantasia' ---")
    try:
        res_vals = client.execute_dax("EVALUATE TOPN(5, VALUES('Competencia'[nome_fantasia]))")
        print("Values (nome_fantasia):", res_vals)
    except:
        print("Could not query nome_fantasia")

    # Check for 'Dias' related columns
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
        print("Error checking days")

    # Check for MEASURES that might be useful
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
