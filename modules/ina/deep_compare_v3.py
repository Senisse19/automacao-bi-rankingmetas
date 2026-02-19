"""
Probe V3: Ajuste fino da lógica de filtros.
Hipótese: Dashboard ignora status_titulo e usa apenas Saldo > 0 e Faixas.
"""

import os
import json
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
load_dotenv(env_path)


class PBI:
    def __init__(self):
        self.tenant = os.environ.get("SHAREPOINT_TENANT")
        self.cid = os.environ.get("POWERBI_CLIENT_ID") or os.environ.get("SHAREPOINT_CLIENT_ID")
        self.csecret = os.environ.get("POWERBI_CLIENT_SECRET") or os.environ.get("SHAREPOINT_CLIENT_SECRET")
        self.ws = os.environ.get("POWERBI_WORKSPACE_ID")
        self.ds = "ae481f4d-b8df-4e0c-915e-47a4606bec06"
        r = requests.post(
            f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.cid,
                "client_secret": self.csecret,
                "scope": "https://analysis.windows.net/powerbi/api/.default",
            },
        )
        self.token = r.json().get("access_token")

    def dax(self, q):
        r = requests.post(
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.ws}/datasets/{self.ds}/executeQueries",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json={
                "queries": [{"query": q}],
                "serializerSettings": {"includeNulls": True},
            },
        )
        try:
            d = r.json()
            if "error" in d:
                return f"ERROR: {json.dumps(d['error'])}"
            return d["results"][0]["tables"][0]["rows"]
        except Exception as e:
            return f"EXC: {e} | RAW: {r.text[:500]}"


c = PBI()

print("=" * 70)
print("PROBE V3: REFINAMENTO DE FILTROS")
print("Data Ref: 11/02/2026")
print("=" * 70)

# KPI INADIMPLÊNCIA TOTAL (Target: 29.639.764)
# Tentativas com faixas de atraso
print("\n--- KPI: INADIMPLÊNCIA TOTAL ---")
queries = [
    # Apenas Ordem 1, 2, 3 (padrão 90 dias)
    (
        "Ordem {1,2,3}",
        "CALCULATE(SUM('Competencia'[valor_contas_receber]), 'Competencia'[area] <> \"InterCompany\", 'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3})",
    ),
    # Ordem 0, 1, 2, 3 (inclui mês vigente/vencendo)
    (
        "Ordem {0,1,2,3}",
        "CALCULATE(SUM('Competencia'[valor_contas_receber]), 'Competencia'[area] <> \"InterCompany\", 'Competencia'[Ordem_Faixa_Atraso] IN {0, 1, 2, 3})",
    ),
    # Ordem >= 1 (tudo atrasado > 0 dias)
    (
        "Ordem >= 1",
        "CALCULATE(SUM('Competencia'[valor_contas_receber]), 'Competencia'[area] <> \"InterCompany\", 'Competencia'[Ordem_Faixa_Atraso] >= 1)",
    ),
    # Tudo atrasado (data < hoje)
    (
        "Vencimento < Hoje",
        "CALCULATE(SUM('Competencia'[valor_contas_receber]), 'Competencia'[area] <> \"InterCompany\", 'Competencia'[data_vencimento] < TODAY())",
    ),
]

dax_parts = [f'"{name}", {expr}' for name, expr in queries]
q = f"EVALUATE ROW({', '.join(dax_parts)})"
r = c.dax(q)

target = 29639764
if isinstance(r, list):
    for k, v in r[0].items():
        v = v or 0
        diff = v - target
        pct = (diff / target * 100) if target else 0
        print(f"  {k:20s}: R$ {v:15,.2f} | Diff: {diff:+12,.0f} ({pct:+.1f}%)")

# CAPRETZ DETALHADO (Target Dashboard: 66.317)
print("\n--- CAPRETZ: DETALHAMENTO ---")
# Recuperar colunas corretas para identificar títulos.
# Tentando 'numero_titulo' ou apenas listagem por valor e vencimento se ID falhar
r = c.dax("""
EVALUATE
CALCULATETABLE(
    SELECTCOLUMNS(
        'Competencia',
        "Status", 'Competencia'[status_titulo],
        "Ordem", 'Competencia'[Ordem_Faixa_Atraso],
        "Valor", 'Competencia'[valor_contas_receber],
        "Vencimento", 'Competencia'[data_vencimento],
        "Dias", DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)
    ),
    CONTAINSSTRING('Competencia'[nome_fantasia], "CAPRETZ"),
    'Competencia'[area] <> "InterCompany"
)
""")
if isinstance(r, list):
    for row in r:
        print(
            f"  Status={row.get('[Status]'):10s} | Ordem={str(row.get('[Ordem]')):3s} | Dias={row.get('[Dias]'):3} | R$ {row.get('[Valor]'):10,.2f}"
        )

# TOP 10 RECALCULADO (Sem filtro de status, apenas Ordem {1,2,3})
print("\n--- TOP 10: Ordem {1,2,3} (Sem Status) ---")
r = c.dax("""
EVALUATE
TOPN(15,
    ADDCOLUMNS(
        CALCULATETABLE(
            VALUES('Competencia'[nome_fantasia]),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        ),
        "Valor", CALCULATE(SUM('Competencia'[valor_contas_receber]), 'Competencia'[area] <> "InterCompany", 'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}),
        "Dias", CALCULATE(MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)), 'Competencia'[area] <> "InterCompany", 'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3})
    ),
    [Valor], DESC
)
""")
if isinstance(r, list):
    for i, row in enumerate(r):
        print(
            f"  {i + 1:2}. {row.get('Competencia[nome_fantasia]')[:25]:25s} | {row.get('[Dias]'):3}d | R$ {row.get('[Valor]'):12,.2f}"
        )
