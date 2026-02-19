import os
import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

# Import ONLY PowerBIClient to avoid other dependencies
from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("debug_simple")

INA_DATASET_ID = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
INA_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID")

client = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)


def run():
    print("--- PROBING COLUMNS IN 'Competencia' ---")

    # Check for likely name columns
    q_cols = """
    SELECT [Name] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND [Name] LIKE '%nome%'
    """
    try:
        res = client.execute_dax(q_cols)
        print("Possible Name Columns:", res)
    except Exception as e:
        print(f"Error cols: {e}")

    # Check distinct values for 'nome_fantasia' to see if masked
    print("\n--- CHECKING VALUES FOR 'nome_fantasia' ---")
    try:
        res_vals = client.execute_dax("EVALUATE TOPN(5, VALUES('Competencia'[nome_fantasia]))")
        print("Values:", res_vals)
    except:
        print("Could not query nome_fantasia")

    # Check for 'Dias' related columns
    print("\n--- CHECKING 'Dias' COLUMNS ---")
    q_days = """
    SELECT [Name] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND [Name] LIKE '%Dias%'
    """
    try:
        res_days = client.execute_dax(q_days)
        print("Possible Days Columns:", res_days)
    except:
        pass


if __name__ == "__main__":
    run()
