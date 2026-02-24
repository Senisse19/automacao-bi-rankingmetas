import dotenv

dotenv.load_dotenv()
from core.clients.powerbi_client import PowerBIClient

client = PowerBIClient()

query = """
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        'ContasReceber'[descricao],
        "V_Outras", [Valor_OutrasReceitas],
        "V_Inter", [Valor_InterCompany],
        "V_SemCat", [Valor_Sem_Categoria]
    ),
    DATESBETWEEN('Calendario'[Date], DATE(2025, 2, 1), DATE(2025, 2, 28))
)
"""

try:
    res = client.execute_dax(query)
    res_sorted = sorted([r for r in res], key=lambda x: str(x.get("ContasReceber[descricao]")))
    with open("outras_detalhes.txt", "w", encoding="utf-8") as f:
        for r in res_sorted:
            if r.get("[V_Outras]") or r.get("[V_Inter]") or r.get("[V_SemCat]"):
                f.write(
                    f"{r.get('ContasReceber[descricao]')}: Outras={r.get('[V_Outras]')}, Inter={r.get('[V_Inter]')}, SemCat={r.get('[V_SemCat]')}\\n"
                )
except Exception as e:
    print("FAILED", e)
