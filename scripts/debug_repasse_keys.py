import dotenv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv.load_dotenv()

from core.clients.powerbi_client import PowerBIClient
from core.services.dax_queries import get_repasses_query

client = PowerBIClient()
client.authenticate()

# Data: Fevereiro/2026
ds = "DATE(2026, 2, 1)"
de = "DATE(2026, 2, 28)"

print("Executando get_repasses_query...")
query = get_repasses_query(ds, de)
res = client.execute_dax(query)

if res:
    row = res[0]
    print(f"Total de chaves retornadas: {len(row)}")
    for k, v in row.items():
        print(f"  {k}: {v}")
else:
    print("Nenhum resultado retornado!")
