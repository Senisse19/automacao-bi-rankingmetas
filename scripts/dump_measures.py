import dotenv

dotenv.load_dotenv()
from core.clients.powerbi_client import PowerBIClient
import json

client = PowerBIClient()
query = "select MEASURE_NAME from $SYSTEM.MDSCHEMA_MEASURES"

try:
    res = client.execute_dax(query)
    names = [x.get("MEASURE_NAME") for x in res if x.get("MEASURE_NAME")]
    with open("all_measures.txt", "w", encoding="utf-8") as f:
        for name in sorted(names):
            f.write(name + "\n")
    print("Saved all measures to all_measures.txt")
except Exception as e:
    print("FAILED", e)
