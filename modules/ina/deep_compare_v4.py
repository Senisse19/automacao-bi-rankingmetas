"""
Probe V4: Investigação dos 'Clientes Fantasmas' (Hiper Neto, Ludfor).
Por que aparecem na base com atraso e valor, mas não no Dashboard?
Status? Natureza?
"""

import os
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
            return d["results"][0]["tables"][0]["rows"]
        except:
            return []


c = PBI()

print("=" * 70)
print("PROBE V4: GHOST CLIENTS (HIPER NETO, LUDFOR)")
print("=" * 70)

clients = ["HIPER NETO", "LUDFOR", "AUTONUNES"]

for client in clients:
    print(f"\n--- {client} ---")
    r = c.dax(f"""
    EVALUATE
    CALCULATETABLE(
        SELECTCOLUMNS(
            'Competencia',
            "Status", 'Competencia'[status_titulo],
            "Valor", 'Competencia'[valor_contas_receber],
            "Ordem", 'Competencia'[Ordem_Faixa_Atraso],
            "Dias", DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)
        ),
        CONTAINSSTRING('Competencia'[nome_fantasia], "{client}"),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
    )
    """)
    for row in r:
        print(
            f"  Status={row.get('[Status]'):12s} | Ordem={str(row.get('[Ordem]')):3s} | R$ {row.get('[Valor]'):10,.2f}"
        )
