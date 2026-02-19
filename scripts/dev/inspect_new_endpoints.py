import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from utils.logger import get_logger

logger = get_logger("inspect_new")


def inspect_new_sources():
    client = JobsClient()

    # IDs de referência do Job 29685

    endpoints = {
        "contratos_recorrentes": "/contratos_recorrentes",
        "servicos": "/servicos",
        "contas_receber": "/contas-receber",
    }

    output = {}

    print("\n--- INSPECIONANDO NOVOS ENDPOINTS ---")

    for name, path in endpoints.items():
        url = f"{client.api_url}{path}"
        print(f"Testing {url} ...")

        try:
            # Tentar filtrar por cliente ou job se possível, senão pega LIMIT 1
            # Vamos tentar params genéricos de filtro first, se falhar pega listagem
            params = {"limit": 1}

            # Tentar adivinhar filtros baseados em padroes comuns (cliente_id, codigo_cliente)
            # Mas primeiro vamos ver estrutura bruta de 1 item

            resp = client.session.get(url, headers=client.headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                item = None
                if isinstance(data, list) and data:
                    item = data[0]
                elif isinstance(data, dict):
                    if "results" in data and data["results"]:
                        item = data["results"][0]
                    elif "data" in data and data["data"]:
                        item = data["data"][0]
                    else:
                        item = data

                if item:
                    print(f"✅ {name}: OK (Amostra coletada)")
                    output[name] = item
                else:
                    print(f"⚠️ {name}: OK (Mas vazio)")
            else:
                print(f"❌ {name}: {resp.status_code}")

        except Exception as e:
            print(f"❌ {name}: Erro {e}")

    # Salvar
    with open("tests/output/new_endpoints_inspection.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    print("\nSalvo em tests/output/new_endpoints_inspection.json")


if __name__ == "__main__":
    inspect_new_sources()
