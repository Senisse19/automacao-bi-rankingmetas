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

print("--- TESTE COM FILTRO DE DEPT_DESCRICAO = 'Repasse' ---")
query_com = get_repasses_query(ds, de)
res_com = client.execute_dax(query_com)
print(f"Resultado Com Filtro: {res_com}")

print("\n--- TESTE SEM FILTRO DE DEPT_DESCRICAO (ROW) ---")
query_sem = f"""
EVALUATE
CALCULATETABLE(
    ROW(
        "Total_Repasse_Geral", [total_repasse],
        "Corporate_Repasse", [Valor_Corporate_Repasse],
        "Tax_Repasse", [valor_Tax_Repasse]
    ),
    DATESBETWEEN('Calendario'[Date], {ds}, {de})
)
"""
res_sem = client.execute_dax(query_sem)
print(f"Resultado Sem Filtro: {res_sem}")
