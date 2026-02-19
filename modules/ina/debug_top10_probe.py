"""Probe: Investigar clientes ausentes do Top 10 (presentes no dashboard mas não na query)."""

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
        d = r.json()
        if "error" in d:
            return f"ERROR: {json.dumps(d['error'], ensure_ascii=False)[:500]}"
        try:
            return d["results"][0]["tables"][0]["rows"]
        except:
            return f"RAW: {json.dumps(d, ensure_ascii=False)[:800]}"


out = []


def log(s):
    out.append(str(s))
    print(s)


c = PBI()

# Clientes ausentes no nosso Top10 mas presentes no dashboard:
missing_clients = ["VITOR M NUNES", "M.B.F", "TOYO INK", "SAWEM"]

gf = """'Competencia'[area] <> "InterCompany", 'Competencia'[status_titulo] IN {"ATRASADO", "A VENCER", "VENCE HOJE"}"""

# P1: Para cada cliente ausente, buscar TODAS as linhas (sem filtro de faixa)
for name in missing_clients:
    log(f"\n{'=' * 60}")
    log(f"=== CLIENTE: {name} ===")
    log(f"{'=' * 60}")

    r = c.dax(f"""
    EVALUATE
    CALCULATETABLE(
        SELECTCOLUMNS(
            'Competencia',
            "nome", 'Competencia'[nome_fantasia],
            "data_venc", 'Competencia'[data_vencimento],
            "valor", 'Competencia'[valor_contas_receber],
            "faixa", 'Competencia'[Faixa_Atraso],
            "status", 'Competencia'[status_titulo],
            "ordem_faixa", 'Competencia'[Ordem_Faixa_Atraso],
            "area", 'Competencia'[area]
        ),
        CONTAINSSTRING('Competencia'[nome_fantasia], "{name}"),
        {gf}
    )
    """)
    if isinstance(r, list):
        log(f"Total linhas: {len(r)}")
        # Agrupar por Ordem_Faixa
        faixas = {}
        total_val = 0
        for row in r:
            of = row.get("[ordem_faixa]", "null")
            faixa = row.get("[faixa]", "null")
            val = row.get("[valor]", 0) or 0
            status = row.get("[status]", "?")
            area = row.get("[area]", "?")
            total_val += val
            key = f"Faixa={faixa} (Ordem={of}) Status={status} Area={area}"
            if key not in faixas:
                faixas[key] = {"count": 0, "total": 0}
            faixas[key]["count"] += 1
            faixas[key]["total"] += val

        log(f"VALOR TOTAL (todas faixas): R$ {total_val:,.2f}")
        log("Detalhes por faixa/status/area:")
        for k, v in sorted(faixas.items()):
            log(f"  {k}: {v['count']} títulos = R$ {v['total']:,.2f}")

        # Valor SOMENTE nas faixas 1,2,3
        val_90 = sum(row.get("[valor]", 0) or 0 for row in r if row.get("[ordem_faixa]") in [1, 2, 3])
        log(f"VALOR FILTRADO (Ordem 1,2,3 apenas): R$ {val_90:,.2f}")
    else:
        log(r)

# P2: Também verificar nossos clientes PRESENTES que NÃO estão no dashboard
log(f"\n{'=' * 60}")
log("=== CLIENTES NO NOSSO TOP10 MAS NAO NO DASHBOARD ===")
log(f"{'=' * 60}")

our_extra = [
    "DEPOSITO DE BEBIDAS",
    "MOINHO HORTOLANDIA",
    "AKSO CONSTRUTORA",
    "NOVA PROSPER",
]
for name in our_extra:
    r = c.dax(f"""
    EVALUATE
    ROW(
        "ValorTotal", CALCULATE(
            SUM('Competencia'[valor_contas_receber]),
            CONTAINSSTRING('Competencia'[nome_fantasia], "{name}"),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        ),
        "MaxDias", CALCULATE(
            MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
            CONTAINSSTRING('Competencia'[nome_fantasia], "{name}"),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        ),
        "Faixas", CALCULATE(
            CONCATENATEX(VALUES('Competencia'[Faixa_Atraso]), 'Competencia'[Faixa_Atraso], " | "),
            CONTAINSSTRING('Competencia'[nome_fantasia], "{name}"),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        )
    )
    """)
    if isinstance(r, list):
        val = r[0].get("[ValorTotal]", 0)
        dias = r[0].get("[MaxDias]", 0)
        faixas = r[0].get("[Faixas]", "?")
        log(f"  {name:30s} | {dias:>5} dias | R$ {val:>12,.2f} | Faixas: {faixas}")
    else:
        log(f"  {name}: {r}")

# P3: Nosso Top 20 completo para ver ranking completo
log(f"\n{'=' * 60}")
log("=== TOP 20 COMPLETO (Ordem_Faixa IN {1,2,3}) ===")
log(f"{'=' * 60}")

r = c.dax(f"""
EVALUATE
TOPN(20,
    ADDCOLUMNS(
        CALCULATETABLE(
            VALUES('Competencia'[nome_fantasia]),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        ),
        "Valor", CALCULATE(
            SUM('Competencia'[valor_contas_receber]),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        ),
        "Dias", CALCULATE(
            MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
            {gf},
            'Competencia'[Ordem_Faixa_Atraso] IN {{1, 2, 3}}
        )
    ),
    [Valor], DESC
)
""")
if isinstance(r, list):
    # Sort by valor DESC
    sorted_r = sorted(r, key=lambda x: float(x.get("[Valor]", 0) or 0), reverse=True)
    for i, row in enumerate(sorted_r):
        nome = str(row.get("Competencia[nome_fantasia]", "?"))[:35]
        valor = row.get("[Valor]", 0) or 0
        dias = row.get("[Dias]", 0)
        log(f"  {i + 1:>2}. {nome:35s} | {dias:>5} dias | R$ {valor:>14,.2f}")
else:
    log(r)

fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_missing.txt")
with open(fp, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print(f"\nSaved: {fp}")
