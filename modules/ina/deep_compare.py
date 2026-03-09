"""
Análise profunda: Automação vs Dashboard — pente fino em cada valor.
Compara KPIs e Top 10 usando queries DAX independentes.
"""

import json
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

# Filtro base igual ao runner.py
gf = '\'Competencia\'[area] <> "InterCompany", \'Competencia\'[status_titulo] IN {"ATRASADO", "A VENCER", "VENCE HOJE"}'
f90 = "'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}"

log("=" * 70)
log("ANÁLISE PROFUNDA: AUTOMAÇÃO vs DASHBOARD")
log("Data da execução: 11/02/2026")
log("=" * 70)

# ====================
# SEÇÃO 1: KPIs
# ====================
log("\n" + "=" * 70)
log("SEÇÃO 1: COMPARAÇÃO DE KPIs")
log("=" * 70)

# KPI 1: Inadimplência Total
r = c.dax(f"""
EVALUATE ROW(
    "Total_SUM", CALCULATE(SUM('Competencia'[valor_contas_receber]), {gf}),
    "Total_SUM_ATRASADO", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "ATRASADO"
    ),
    "Total_COUNT", CALCULATE(COUNTROWS('Competencia'), {gf}),
    "Total_COUNT_ATRASADO", CALCULATE(
        COUNTROWS('Competencia'),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "ATRASADO"
    )
)
""")
if isinstance(r, list):
    total_all = r[0].get("[Total_SUM]", 0)
    total_atrasado = r[0].get("[Total_SUM_ATRASADO]", 0)
    count_all = r[0].get("[Total_COUNT]", 0)
    count_atrasado = r[0].get("[Total_COUNT_ATRASADO]", 0)
    log("\n  INADIMPLÊNCIA TOTAL:")
    log("  Dashboard:     R$ 29.639.764")
    log(f"  Automação:     R$ {total_all:,.2f}  (filtro: area<>IC + status IN ATRASADO/A VENCER/VENCE HOJE)")
    log(f"  Só ATRASADO:   R$ {total_atrasado:,.2f}  (filtro: area<>IC + status = ATRASADO)")
    log(f"  Diferença:     R$ {total_all - 29639764:,.2f}")
    log(f"  Count All:     {count_all} títulos | Count ATRASADO: {count_atrasado} títulos")
else:
    log(r)

# KPI 2: Vencendo Hoje
r = c.dax("""
EVALUATE ROW(
    "VencendoHoje", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "VENCE HOJE"
    )
)
""")
if isinstance(r, list):
    vh = r[0].get("[VencendoHoje]", 0)
    log("\n  VENCENDO HOJE:")
    log("  Dashboard:     R$ 4.247")
    log(f"  Automação:     R$ {vh:,.2f}")

# KPI 3: Conciliação
r = c.dax("""
EVALUATE ROW(
    "Conciliacao_AVENCER", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "A VENCER"
    ),
    "Conciliacao_2DAYS", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "A VENCER",
        'Competencia'[data_vencimento] <= TODAY() + 2
    )
)
""")
if isinstance(r, list):
    conc_avencer = r[0].get("[Conciliacao_AVENCER]", 0)
    conc_2d = r[0].get("[Conciliacao_2DAYS]", 0)
    log("\n  CONCILIAÇÃO (D+2):")
    log("  Dashboard:     R$ 347.654")
    log(f"  A VENCER total:R$ {conc_avencer:,.2f}")
    log(f"  A VENCER <=D+2:R$ {conc_2d:,.2f}")

# KPI 4: Média Atraso
r = c.dax(f"""
EVALUATE ROW(
    "Media_AVG", CALCULATE(
        AVERAGEX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
        {gf}
    ),
    "Media_ATRASADO", CALCULATE(
        AVERAGEX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
        'Competencia'[area] <> "InterCompany",
        'Competencia'[status_titulo] = "ATRASADO"
    )
)
""")
if isinstance(r, list):
    media_all = r[0].get("[Media_AVG]", 0)
    media_atr = r[0].get("[Media_ATRASADO]", 0)
    log("\n  MÉDIA ATRASO:")
    log(f"  Automação avg(todos):   {media_all:.0f} dias")
    log(f"  Automação avg(atrasado):{media_atr:.0f} dias")

# ====================
# SEÇÃO 2: TOP 10 DETALHADO
# ====================
log("\n" + "=" * 70)
log("SEÇÃO 2: TOP 10 — COMPARAÇÃO DETALHADA")
log("=" * 70)

# Dashboard Top 10 (transcrito do screenshot)
dashboard_top10 = [
    ("FRIPREMIUM COMERCIAL", 68, 10179634),
    ("GUILHERME QUEIROZ LIMA", 54, 111182),
    ("VITOR M NUNES FILHO", 6, 100000),
    ("FOCO EMPRESARIAL 360", 58, 68500),
    ("CAPRETZ EMPREENDIMEN", 13, 66317),
    ("CATA TECIDOS E EMBALAG", 65, 47247),
    ("TOYO INK BRASIL LTDA", 6, 44108),
    ("SAWEM DA AMAZONIA", 54, 43097),
    ("FINEC SOLUCOES JURIDICA", 68, 41072),
    ("SAWEM INDUSTRIAL", 5, 35447),
]

# Nossa query Top 20
r = c.dax(f"""
EVALUATE
TOPN(20,
    ADDCOLUMNS(
        CALCULATETABLE(
            VALUES('Competencia'[nome_fantasia]),
            {gf},
            {f90}
        ),
        "Valor", CALCULATE(
            SUM('Competencia'[valor_contas_receber]),
            {gf}, {f90}
        ),
        "Dias", CALCULATE(
            MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
            {gf}, {f90}
        ),
        "CountTitulos", CALCULATE(
            COUNTROWS('Competencia'),
            {gf}, {f90}
        )
    ),
    [Valor], DESC
)
""")

our_top20 = []
if isinstance(r, list):
    for row in r:
        nome = row.get("Competencia[nome_fantasia]", "?")
        valor = row.get("[Valor]", 0) or 0
        dias = row.get("[Dias]", 0)
        count = row.get("[CountTitulos]", 0)
        our_top20.append({"nome": nome, "valor": valor, "dias": dias, "count": count})
    our_top20.sort(key=lambda x: x["valor"], reverse=True)

log("\nNosso Top 20 (com contagem de títulos):")
for i, item in enumerate(our_top20):
    log(
        f"  {i + 1:>2}. {item['nome'][:40]:40s} | {item['dias']:>4}d | R$ {item['valor']:>14,.2f} | {item['count']} títulos"
    )

# Comparação direta
log(f"\n{'=' * 70}")
log("COMPARAÇÃO LINHA A LINHA")
log(f"{'=' * 70}")
log(f"{'#':>3} | {'Dashboard':40s} | {'Valor DB':>14} | {'Nosso Valor':>14} | {'Diff':>12} | Status")
log("-" * 130)

our_dict = {item["nome"][:20].upper().strip(): item for item in our_top20}

for i, (d_nome, d_dias, d_valor) in enumerate(dashboard_top10):
    d_nome_key = d_nome[:20].upper().strip()
    match = None
    for k, v in our_dict.items():
        if d_nome_key[:10] in k or k[:10] in d_nome_key:
            match = v
            break

    if match:
        diff = match["valor"] - d_valor
        pct = (diff / d_valor * 100) if d_valor else 0
        status = "✅" if abs(pct) < 1 else f"⚠️ {pct:+.1f}%"
        log(
            f"  {i + 1:>2} | {d_nome:40s} | R$ {d_valor:>12,} | R$ {match['valor']:>12,.0f} | R$ {diff:>+10,.0f} | {status}"
        )
    else:
        log(f"  {i + 1:>2} | {d_nome:40s} | R$ {d_valor:>12,} | {'NÃO ENCONTR':>14} | {'---':>12} | ❌ AUSENTE")

# Investigar clientes divergentes individualmente
log(f"\n{'=' * 70}")
log("SEÇÃO 3: INVESTIGAÇÃO DE CLIENTES DIVERGENTES")
log(f"{'=' * 70}")

# CAPRETZ - grande divergência
for client in ["CAPRETZ", "VITOR M NUNES", "TOYO INK", "SAWEM"]:
    log(f"\n--- {client} ---")
    r = c.dax(f"""
    EVALUATE
    CALCULATETABLE(
        SUMMARIZECOLUMNS(
            'Competencia'[status_titulo],
            'Competencia'[Faixa_Atraso],
            'Competencia'[Ordem_Faixa_Atraso],
            "Valor", SUM('Competencia'[valor_contas_receber]),
            "Count", COUNTROWS('Competencia'),
            "MaxDias", MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY))
        ),
        CONTAINSSTRING('Competencia'[nome_fantasia], "{client}"),
        'Competencia'[area] <> "InterCompany"
    )
    """)
    if isinstance(r, list):
        for row in r:
            status = row.get("Competencia[status_titulo]", "?")
            faixa = row.get("Competencia[Faixa_Atraso]", "?")
            ordem = row.get("Competencia[Ordem_Faixa_Atraso]", "?")
            valor = row.get("[Valor]", 0) or 0
            count = row.get("[Count]", 0)
            maxd = row.get("[MaxDias]", 0)
            in90 = "✅ IN" if ordem in [1, 2, 3] else "❌ OUT"
            log(
                f"  Status={status:12s} | Faixa={str(faixa):20s} | Ordem={ordem} {in90} | {count:>3} tit | R$ {valor:>12,.2f} | MaxDias={maxd}"
            )
    else:
        log(f"  {r}")

# SEÇÃO 4: Verificar se filtro global exclui títulos que dashboard inclui
log(f"\n{'=' * 70}")
log("SEÇÃO 4: TOTAL SEM FILTRO DE STATUS vs COM FILTRO")
log(f"{'=' * 70}")

r = c.dax(f"""
EVALUATE ROW(
    "Total_SemFiltroStatus", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        'Competencia'[area] <> "InterCompany"
    ),
    "Total_ComFiltroStatus", CALCULATE(
        SUM('Competencia'[valor_contas_receber]),
        {gf}
    ),
    "Count_SemFiltroStatus", CALCULATE(
        COUNTROWS('Competencia'),
        'Competencia'[area] <> "InterCompany"
    ),
    "Count_ComFiltroStatus", CALCULATE(
        COUNTROWS('Competencia'), {gf}
    )
)
""")
if isinstance(r, list):
    tsem = r[0].get("[Total_SemFiltroStatus]", 0)
    tcom = r[0].get("[Total_ComFiltroStatus]", 0)
    csem = r[0].get("[Count_SemFiltroStatus]", 0)
    ccom = r[0].get("[Count_ComFiltroStatus]", 0)
    log(f"  Sem filtro status: R$ {tsem:,.2f} ({csem} títulos)")
    log(f"  Com filtro status: R$ {tcom:,.2f} ({ccom} títulos)")
    log(f"  Diferença:         R$ {tsem - tcom:,.2f} ({csem - ccom} títulos)")

fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep_compare_results.txt")
with open(fp, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print(f"\nSaved: {fp}")
