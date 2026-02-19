"""
Probe final: descobrir o filtro EXATO que o dashboard usa.
Testa hipóteses específicas para cada KPI.
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
        d = r.json()
        if "error" in d:
            return f"ERROR: {json.dumps(d['error'], ensure_ascii=False)[:500]}"
        try:
            return d["results"][0]["tables"][0]["rows"]
        except:
            return f"RAW: {json.dumps(d, ensure_ascii=False)[:800]}"


c = PBI()

print("=" * 70)
print("HIPÓTESES PARA INADIMPLÊNCIA TOTAL (Dashboard: R$ 29.639.764)")
print("=" * 70)

# Hipótese 1: Só ATRASADO
# Hipótese 2: ATRASADO + A VENCER
# Hipótese 3: ATRASADO + VENCE HOJE
# Hipótese 4: Só faixas 1-6 (sem "acima de X")
# Hipótese 5: Usa medida calculada com filtro de data_vencimento < TODAY()
# Hipótese 6: Filtro por Ordem_Faixa_Atraso (excluindo 0 e nulls)

r = c.dax("""
EVALUATE ROW(
    "H1_ATRASADO", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "ATRASADO"
    ),
    "H2_ATRASADO_AVENCER", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] IN {"ATRASADO", "A VENCER"}
    ),
    "H3_ATRASADO_VENCHOJE", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] IN {"ATRASADO", "VENCE HOJE"}
    ),
    "H4_VencimentoPast", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[data_vencimento] < TODAY()
    ),
    "H5_Ordem_GT0", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] > 0
    ),
    "H6_Ordem_GE1", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] >= 1
    )
)
""")

target = 29639764
if isinstance(r, list):
    for k, v in r[0].items():
        v = v or 0
        diff = v - target
        pct = (diff / target * 100) if target else 0
        match = "✅ MATCH!" if abs(pct) < 0.5 else ""
        print(f"  {k:30s} = R$ {v:>14,.2f} | Diff: R$ {diff:>+12,.0f} ({pct:+.2f}%) {match}")
else:
    print(r)

# Top 10 com filtro Ordem >= 1 (exclui Mês Vigente=0 e nulls)
print("\n" + "=" * 70)
print("HIPÓTESES PARA CONCILIAÇÃO (Dashboard: R$ 347.654)")
print("=" * 70)

r = c.dax("""
EVALUATE ROW(
    "C1_AVENCER_d2", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "A VENCER",
        'Competencia'[data_vencimento] <= TODAY() + 2,
        'Competencia'[data_vencimento] > TODAY()
    ),
    "C2_Ordem0", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] = 0
    ),
    "C3_Ordem0_AVENCER", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] = 0,
        'Competencia'[status_titulo] = "A VENCER"
    ),
    "C4_VENCHOJE_AVENCER_Ordem0", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] IN {"VENCE HOJE", "A VENCER"},
        'Competencia'[Ordem_Faixa_Atraso] = 0
    )
)
""")
target_c = 347654
if isinstance(r, list):
    for k, v in r[0].items():
        v = v or 0
        diff = v - target_c
        pct = (diff / target_c * 100) if target_c else 0
        match = "✅ MATCH!" if abs(pct) < 1 else ""
        print(f"  {k:40s} = R$ {v:>14,.2f} | Diff: R$ {diff:>+12,.0f} ({pct:+.2f}%) {match}")
else:
    print(r)

# Top 10 com filtro ATRASADO *apenas*
print("\n" + "=" * 70)
print("TOP 10 SÓ COM FILTRO ATRASADO (hipótese dashboard)")
print("=" * 70)

r = c.dax("""
EVALUATE
TOPN(10,
    ADDCOLUMNS(
        CALCULATETABLE(
            VALUES('Competencia'[nome_fantasia]),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[status_titulo] = "ATRASADO",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        ),
        "Valor", CALCULATE(
            SUM('Competencia'[valor_contas_receber]),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[status_titulo] = "ATRASADO",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        ),
        "Dias", CALCULATE(
            MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[status_titulo] = "ATRASADO",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        )
    ),
    [Valor], DESC
)
""")
if isinstance(r, list):
    items = sorted(r, key=lambda x: x.get("[Valor]", 0) or 0, reverse=True)
    for i, row in enumerate(items):
        nome = row.get("Competencia[nome_fantasia]", "?")
        valor = row.get("[Valor]", 0) or 0
        dias = row.get("[Dias]", 0)
        print(f"  {i + 1:>2}. {nome[:40]:40s} | {dias:>4}d | R$ {valor:>14,.2f}")

# Top 10 sem filtro de status, todos os Ordem >= 1
print("\n" + "=" * 70)
print("TOP 10 SEM FILTRO STATUS, Ordem >= 1")
print("=" * 70)

r = c.dax("""
EVALUATE
TOPN(10,
    ADDCOLUMNS(
        CALCULATETABLE(
            VALUES('Competencia'[nome_fantasia]),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        ),
        "Valor", CALCULATE(
            SUM('Competencia'[valor_contas_receber]),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        ),
        "Dias", CALCULATE(
            MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
            'Competencia'[area] <> "InterCompany",
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        )
    ),
    [Valor], DESC
)
""")
if isinstance(r, list):
    items = sorted(r, key=lambda x: x.get("[Valor]", 0) or 0, reverse=True)
    for i, row in enumerate(items):
        nome = row.get("Competencia[nome_fantasia]", "?")
        valor = row.get("[Valor]", 0) or 0
        dias = row.get("[Dias]", 0)
        print(f"  {i + 1:>2}. {nome[:40]:40s} | {dias:>4}d | R$ {valor:>14,.2f}")

# CAPRETZ: entender porque dashboard diz R$ 66.317 e nós temos R$ 120.576
print("\n" + "=" * 70)
print("CAPRETZ: BREAKDOWN TÍTULO A TÍTULO")
print("=" * 70)

r = c.dax("""
EVALUATE
CALCULATETABLE(
    SELECTCOLUMNS(
        'Competencia',
        "NF", 'Competencia'[titulo],
        "Status", 'Competencia'[status_titulo],
        "Faixa", 'Competencia'[Faixa_Atraso],
        "Ordem", 'Competencia'[Ordem_Faixa_Atraso],
        "Valor", 'Competencia'[valor_contas_receber],
        "Vencimento", 'Competencia'[data_vencimento],
        "DiasCalc", DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)
    ),
    CONTAINSSTRING('Competencia'[nome_fantasia], "CAPRETZ"),
    'Competencia'[area] <> "InterCompany"
)
""")
if isinstance(r, list):
    total = 0
    for row in r:
        nf = row.get("[NF]", "?")
        st = row.get("[Status]", "?")
        fx = row.get("[Faixa]", "?")
        od = row.get("[Ordem]", "?")
        vl = row.get("[Valor]", 0) or 0
        vc = str(row.get("[Vencimento]", "?"))[:10]
        dc = row.get("[DiasCalc]", 0)
        total += vl
        print(f"  NF={nf:20s} | {st:12s} | Faixa={str(fx):16s} | Ord={od} | R$ {vl:>12,.2f} | Venc={vc} | Dias={dc}")
    print(f"  TOTAL: R$ {total:,.2f}")
else:
    print(r)

# FRIPREMIUM: entender a diff de R$ 4.546
print("\n" + "=" * 70)
print("FRIPREMIUM: SUM COM DIFERENTES FILTROS")
print("=" * 70)
r = c.dax("""
EVALUATE ROW(
    "SemFiltroStatus", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        CONTAINSSTRING('Competencia'[nome_fantasia], "FRIPREMIUM"),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
    ),
    "SoAtrasado", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        CONTAINSSTRING('Competencia'[nome_fantasia], "FRIPREMIUM"),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "ATRASADO",
        'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
    ),
    "Todos3Status", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        CONTAINSSTRING('Competencia'[nome_fantasia], "FRIPREMIUM"),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] IN {"ATRASADO", "A VENCER", "VENCE HOJE"},
        'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
    )
)
""")
if isinstance(r, list):
    for k, v in r[0].items():
        v = v or 0
        print(f"  {k:25s} = R$ {v:>14,.2f}")
