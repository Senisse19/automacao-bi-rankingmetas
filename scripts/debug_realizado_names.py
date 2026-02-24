import dotenv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv.load_dotenv()

from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()
client.authenticate()

ds = "DATE(2026, 2, 1)"
de = "DATE(2026, 2, 28)"

measures = [
    ("Realizado GS", "[Realizado GS]"),
    ("Total_GS", "[Total_GS]"),
    ("Comercial", "[Comercial]"),
    ("Operacional", "[Operacional]"),
    ("Corporate", "[Corporate]"),
    ("Educacao", "[Educacao]"),
    ("Expansao", "[Expansao]"),
    ("Franchising", "[Franchising]"),
    ("PJ", "[PJ]"),
    ("Tax", "[Tax]"),
    ("Comercial_Total", "[Comercial_Total]"),
    ("Operacional_Total", "[Operacional_Total]"),
]

print("Verificando medidas de Realizado...")
for nickname, m in measures:
    q = f"EVALUATE ROW('{nickname}', {m})"
    try:
        res = client.execute_dax(q)
        val = res[0].get(nickname) if res else "N/A"
        print(f"  {nickname:20}: {val}")
    except Exception as e:
        print(f"  {nickname:20}: ERRO ({str(e)[:50]})")
