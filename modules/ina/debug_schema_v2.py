import os
import sys

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("debug_schema")

INA_DATASET_ID = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
INA_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID")

client = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)


def run():
    # Query to get columns of 'Competencia' table to find name and days
    # Also check if there is a 'Clientes' table
    query = """
    SELECT * 
    FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (
        SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia'
    )
    OR [TableID] IN (
        SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Clientes'
    )
    """

    print("Executing query...")
    try:
        result = client.execute_dax(query)
        if result:
            print("\n--- COLUMNS FOUND ---")
            for row in result:
                print(
                    f"Table: {row.get('Parent_Name', 'Unknown')} | Column: {row.get('Name')} | ExplicitName: {row.get('ExplicitName')}"
                )
        else:
            print("No columns found.")
    except Exception as e:
        print(f"Error: {e}")

    # Also try to preview distinct values of 'nome_fantasia' to see if it is indeed 'Anônimo'
    print("\n--- CHECKING NAMES ---")
    q_names = """
    EVALUATE
    TOPN(5, VALUES('Competencia'[nome_fantasia]))
    """
    try:
        res_names = client.execute_dax(q_names)
        print(res_names)
    except Exception as e:
        print(f"Error names: {e}")


if __name__ == "__main__":
    run()
