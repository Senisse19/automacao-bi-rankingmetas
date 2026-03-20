import argparse
import json
import os
import sys
from datetime import date

# Adiciona o diretório raiz do projeto ao sys.path para importações locais
# assume que o script está em studio-automation-core/scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.config import POWERBI_CONFIG
from src.core.clients.powerbi_client import PowerBIClient
from src.core.services import dax_queries


def get_date_range():
    """Retorna o range de datas formatado para DAX (Início do mês até hoje)."""
    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    # Formato DAX: DATE(YYYY, MM, DD)
    dax_start = start_of_month.strftime("DATE(%Y, %m, %d)")
    dax_end = today.strftime("DATE(%Y, %m, %d)")

    return dax_start, dax_end

def fetch_data(dashboard_id: str):
    """Mapeia o dashboard para a query e dataset correspondente."""
    dax_start, dax_end = get_date_range()

    # Mapping simplificado para o Agente de IA
    if "comercial" in dashboard_id.lower() or "metas" in dashboard_id.lower():
        dataset_id = POWERBI_CONFIG.get("metas_dataset_id")
        query = dax_queries.get_receitas_liquido_query(dax_start, dax_end)
    elif "ina" in dashboard_id.lower() or "inadimplencia" in dashboard_id.lower():
        dataset_id = POWERBI_CONFIG.get("ina_dataset_id")
        query = dax_queries.get_metas_com_op_query(dax_start, dax_end) # Ajustar para query de INA real se disponível
    elif "unidades" in dashboard_id.lower():
        dataset_id = POWERBI_CONFIG.get("unidades_dataset_id")
        query = dax_queries.get_unidades_summary_query(dax_start, dax_end)
    else:
        # Fallback para o dataset principal se não houver match
        dataset_id = POWERBI_CONFIG.get("workspace_id") # Use workspace_id as placeholder
        query = f"EVALUATE ROW('Status', 'Dashboard {dashboard_id} não reconhecido no mapeamento')"

    if not dataset_id:
        return {"error": f"Dataset ID não configurado para {dashboard_id}"}

    try:
        client = PowerBIClient(dataset_id=dataset_id)
        results = client.execute_dax(query)
        return results if results else []
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Busca dados do Power BI para o Agente de IA do n8n")
    parser.add_argument("--dashboard", required=True, help="ID ou Nome do dashboard (ex: metas, ina)")
    args = parser.parse_args()

    data = fetch_data(args.dashboard)

    # Printe o JSON para o n8n capturar via stdout
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
