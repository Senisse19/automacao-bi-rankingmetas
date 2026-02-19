import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from utils.logger import get_logger

logger = get_logger("inspect_rel")


def inspect_relations():
    client = JobsClient()

    # IDs coletados do job 29685
    cliente_id = 16048
    produto_id = 115
    franqueado_id = 7066

    output = {}

    endpoints = {
        "cliente": f"/clientes/{cliente_id}",
        "produto": f"/produtos/{produto_id}",
        "franqueado": f"/franqueados/{franqueado_id}",
        "unidade": "/unidades/535",  # Do JSON anterior
    }

    print("\n--- TESTANDO ENDPOINTS RELACIONADOS ---")

    for name, path in endpoints.items():
        url = f"{client.api_url}{path}"
        print(f"GET {url} ...")
        try:
            resp = client.session.get(url, headers=client.headers)
            if resp.status_code == 200:
                print(f"✅ {name}: OK")
                output[name] = resp.json()
            else:
                print(f"❌ {name}: {resp.status_code}")
                # Tentar plural ou singular diferente?
                # Talvez 'clientes' vs 'clients'? Nexus geralmente é pt-br.
        except Exception as e:
            print(f"❌ {name}: Erro {e}")

    # Salvar
    with open("tests/output/relations_inspection.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    print("\nSalvo em tests/output/relations_inspection.json")


if __name__ == "__main__":
    inspect_relations()
