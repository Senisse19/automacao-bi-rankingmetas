"""
Script de diagnóstico — testa medidas de liquido e tenta descobrir medidas de repasse.
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

from core.clients.powerbi_client import PowerBIClient
from datetime import datetime, timedelta

client = PowerBIClient()
client.authenticate()

now = datetime.now()
s = datetime(now.year, now.month, 1)
e = (
    datetime(now.year, now.month + 1, 1) - timedelta(days=1)
    if now.month < 12
    else datetime(now.year + 1, 1, 1) - timedelta(days=1)
)
ds = f"DATE({s.year}, {s.month}, {s.day})"
de = f"DATE({e.year}, {e.month}, {e.day})"

url = f"https://api.powerbi.com/v1.0/myorg/groups/{client.workspace_id}/datasets/{client.dataset_id}/executeQueries"
headers = {"Authorization": f"Bearer {client.token}", "Content-Type": "application/json"}


def test_measure(label, dax_name):
    """Testa medida individualmente e exibe resultado ou erro."""
    q = f"""
    EVALUATE
    CALCULATETABLE(
        ROW("v", [{dax_name}]),
        DATESBETWEEN('Calendario'[Date], {ds}, {de})
    )
    """
    r = requests.post(
        url, json={"queries": [{"query": q}], "serializerSettings": {"includeNulls": True}}, headers=headers, timeout=15
    )
    if r.ok:
        rows = r.json().get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
        val = list(rows[0].values())[0] if rows else "(vazio)"
        print(f"  ✅ [{dax_name}] = {val}")
        return True
    else:
        txt = r.text
        if "cannot be determined" in txt:
            start = txt.find("'<oii>") + 6
            end = txt.find("</oii>'", start)
            bad = txt[start:end] if start > 6 else dax_name
            print(f"  ❌ [{dax_name}] → '{bad}' NÃO EXISTE")
        else:
            print(f"  ❌ [{dax_name}] → HTTP {r.status_code}")
        return False


print("\n=== LÍQUIDOS (nomes confirmados no modelo) ===")
test_measure("corporate", "corporate_liquido")
test_measure("educacao", "educacao_liquido")
test_measure("expansao", "expansao_liquido")
test_measure("franchising", "franchising_liquido")
test_measure("tax", "tax_liquido")
test_measure("pj/tecnologia", "tecnlogia_liquido")
test_measure("total_com", "total_liquido_comercial")
test_measure("total_op", "total_liquido_operacao")

print("\n=== REPASSES (tentativas de nomes prováveis) ===")
# Tenta variações comuns do nome
candidates = [
    "repasse_corporate",
    "Repasse_Corporate",
    "REPASSE_CORPORATE",
    "corporate_repasse",
    "Corporate_Repasse",
    "repasse_tax",
    "tax_repasse",
    "Tax_Repasse",
    "repasse_total",
    "Total_Repasse",
    "total_repasse",
    "Valor_Repasse_Corporate",
    "valor_repasse_corporate",
    "repasse",
    "Repasse",
    "REPASSE",
]
for c in candidates:
    test_measure(c, c)
