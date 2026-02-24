import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()
client.authenticate()

# Data filter: February 2026 up to the 28th
ds = "DATE(2026, 2, 1)"
de = "DATE(2026, 2, 28)"

url = f"https://api.powerbi.com/v1.0/myorg/groups/{client.workspace_id}/datasets/{client.dataset_id}/executeQueries"
headers = {"Authorization": f"Bearer {client.token}", "Content-Type": "application/json"}


def run_single(name, measure):
    q = f"""
    EVALUATE
    CALCULATETABLE(
        ROW("{name}", {measure}),
        DATESBETWEEN('Calendario'[Date], {ds}, {de})
    )
    """
    r = requests.post(
        url, json={"queries": [{"query": q}], "serializerSettings": {"includeNulls": True}}, headers=headers, timeout=20
    )
    if r.ok:
        rows = r.json().get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
        if rows:
            v = rows[0].get(f"[{name}]")
            if v is not None and isinstance(v, (int, float)):
                print(f"{name:30} = {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            else:
                print(f"{name:30} = {v}")
        else:
            print(f"{name:30} = (sem dados)")
    else:
        txt = r.text
        print(f"{name:30} = ERRO: {txt[:100]}")


measures = [
    ("Realizado GS", "[Realizado GS]"),
    ("Total_GS", "[Total_GS]"),
    ("Comercial_Total", "[Comercial_Total]"),
    ("Operacional_Total", "[Operacional_Total]"),
    ("valor_Tax", "[valor_Tax]"),
    ("Valor_Corporate", "[Valor_Corporate]"),
    ("Valor_Expansao", "[Valor_Expansao]"),
    ("Valor_Franchising", "[Valor_Franchising]"),
    ("Valor_Educacao", "[Valor_Educacao]"),
    ("Valor_PJ", "[Valor_PJ]"),
    # Repasses
    ("valor_Tax_Repasse", "[valor_Tax_Repasse]"),
    ("Valor_Corporate_Repasse", "[Valor_Corporate_Repasse]"),
    ("Valor_Expansao_Repasse", "[Valor_Expansao_Repasse]"),
    ("Valor_Franchising_Repasse", "[Valor_Franchising_Repasse]"),
    ("Valor_Educacao_Repasse", "[Valor_Educacao_Repasse]"),
    ("Valor_PJ_Repasse", "[Valor_PJ_Repasse]"),
    ("total_repasse", "[total_repasse]"),
    # Liquido
    ("tax_liquido", "[tax_liquido]"),
    ("corporate_liquido", "[corporate_liquido]"),
    ("expansao_liquido", "[expansao_liquido]"),
    ("franchising_liquido", "[franchising_liquido]"),
    ("educacao_liquido", "[educacao_liquido]"),
    ("tecnlogia_liquido", "[tecnlogia_liquido]"),
    ("total_liquido_comercial", "[total_liquido_comercial]"),
    ("total_liquido_operacao", "[total_liquido_operacao]"),
    # Receitas
    ("Valor_InterCompany", "[Valor_InterCompany]"),
    ("VALOR_OUTRAS_RECEITAS", "[VALOR_OUTRAS_RECEITAS]"),
    ("TOTAL_2", "[TOTAL_2]"),
]

print("=== VERIFICACAO DIRETA DAS MEDIDAS NO NOVO DATASET ===")
for name, measure in measures:
    run_single(name, measure)
