import dotenv

dotenv.load_dotenv()
from core.clients.powerbi_client import PowerBIClient
import json

client = PowerBIClient()
query = "SELECT TABLE_NAME, COLUMN_NAME FROM $SYSTEM.MDSCHEMA_COLUMNS"

try:
    res = client.execute_dax(query)
    with open("all_columns.txt", "w", encoding="utf-8") as f:
        for row in res:
            t_name = row.get("TABLE_NAME") or ""
            c_name = row.get("COLUMN_NAME") or ""
            if not t_name.startswith("RowNumber"):
                f.write(f"{t_name} -> {c_name}\\n")
    print("Saved to all_columns.txt")
except Exception as e:
    print("FAILED", e)
