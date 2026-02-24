"""
Lista as bandeiras reais dos registros com descricao relacionada a 'REPASSE'
para entender como mapear por departamento.
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
if now.month < 12:
    e = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
else:
    e = datetime(now.year + 1, 1, 1) - timedelta(days=1)
ds = f"DATE({s.year}, {s.month}, {s.day})"
de_s = f"DATE({e.year}, {e.month}, {e.day})"

url = f"https://api.powerbi.com/v1.0/myorg/groups/{client.workspace_id}/datasets/{client.dataset_id}/executeQueries"
headers = {"Authorization": f"Bearer {client.token}", "Content-Type": "application/json"}


def run(label, q, multi=False):
    r = requests.post(
        url,
        json={"queries": [{"query": q}], "serializerSettings": {"includeNulls": True}},
        headers=headers,
        timeout=20,
    )
    if r.ok:
        rows = r.json().get("results", [{}])[0].get("tables", [{}])[0].get("rows", [])
        if rows:
            if multi:
                print(f"\n  [{label}]:")
                for row in rows:
                    vals = " | ".join(f"{k}={v}" for k, v in row.items())
                    print(f"    {vals}")
            else:
                val = list(rows[0].values())[0]
                print(f"  {label}: {val}")
        else:
            print(f"  {label}: (sem dados)")
    else:
        print(f"  ERR [{label}]: HTTP {r.status_code}")


# Listamos as bandeiras + valores dos registros com descricao='REPASSE' no mês corrente
print("\n=== Bandeiras com descricao='REPASSE' no mês atual ===")
run(
    "bandeiras_repasse",
    f"""
EVALUATE
SUMMARIZECOLUMNS(
    ContasReceber[bandeira],
    ContasReceber[descricao],
    FILTER(
        DATESBETWEEN('Calendario'[Date], {ds}, {de_s}) && ContasReceber[descricao] = "REPASSE"
    ),
    "Total", SUM(ContasReceber[valor_conta_corrente])
)
""",
    multi=True,
)

# Tenta via SUMMARIZE com bandeira
print("\n=== SUMMARIZE de REPASSE por bandeira ===")
run(
    "summarize_repasse_bandeira",
    f"""
EVALUATE
CALCULATETABLE(
    SUMMARIZE(
        ContasReceber,
        ContasReceber[bandeira],
        "repasse", SUM(ContasReceber[valor_conta_corrente])
    ),
    DATESBETWEEN('Calendario'[Date], {ds}, {de_s}),
    ContasReceber[descricao] = "REPASSE"
)
""",
    multi=True,
)

# Lista descrições que contêm "REPASSE" para descobrir variações
print("\n=== Descrições com REPASSE no nome ===")
run(
    "desc_com_repasse",
    f"""
EVALUATE
CALCULATETABLE(
    SUMMARIZE(
        ContasReceber,
        ContasReceber[descricao],
        "total", SUM(ContasReceber[valor_conta_corrente])
    ),
    DATESBETWEEN('Calendario'[Date], {ds}, {de_s}),
    SEARCH("REPASSE", ContasReceber[descricao], 1, 0) > 0
)
""",
    multi=True,
)
