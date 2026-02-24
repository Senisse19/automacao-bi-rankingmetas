import dotenv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv.load_dotenv()

from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()
client.authenticate()

# List measures from DMVs
query = "SELECT [MEASURE_NAME], [EXPRESSION] FROM $SYSTEM.MDSCHEMA_MEASURES WHERE [MEASURE_VISIBILITY] = True"
res = client.execute_dax(query)

if res:
    print(f"Total de medidas encontradas: {len(res)}")
    for row in res:
        name = row.get("MEASURE_NAME")
        if any(
            x in name.lower()
            for x in [
                "comercial",
                "operacional",
                "corporate",
                "educacao",
                "expansao",
                "franchising",
                "pj",
                "tax",
                "repasse",
                "liquido",
                "meta",
            ]
        ):
            print(f"  Measure: {name}")
else:
    print("Nenhuma medida encontrada!")
