import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from utils.logger import get_logger

logger = get_logger("inspect_contracts")


def inspect_contracts():
    client = JobsClient()

    attempts = [
        {
            "url": f"{client.api_url}/contratos_recorrentes/",
            "method": "GET",
            "desc": "GET com barra final (User Recommendation)",
        },
        {
            "url": f"{client.api_url}/contratos_recorrentes/",
            "method": "POST",
            "desc": "POST com barra final",
        },
    ]

    for attempt in attempts:
        url = attempt["url"]
        method = attempt["method"]
        print(f"\n🔍 Tentando: {method} {url} ({attempt['desc']})")

        try:
            if method == "GET":
                resp = client.session.get(url, headers=client.headers, params={"limit": 1})
            else:
                # POST sem payload complexo, talvez apenas vazio
                payload = {}
                print(f"Enviando payload simples: {payload}")
                resp = client.session.post(url, headers=client.headers, json=payload)

            print(f"Status Code: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print("✅ SUCESSO!")

                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("results") or data.get("data") or []

                if items:
                    print(f"Encontrados {len(items)} itens.")
                    with open("tests/output/contract_sample.json", "w", encoding="utf-8") as f:
                        json.dump(items[0], f, indent=4, ensure_ascii=False)
                    print("📝 Amostra salva em tests/output/contract_sample.json")
                    print("\nCampos Disponíveis:")
                    print(list(items[0].keys()))
                    return  # Sucesso, para aqui
                else:
                    print("⚠️ Retornou vazio.")
            else:
                print(f"❌ Falha: {resp.text[:200]}")  # Limitar msg erro

        except Exception as e:
            print(f"❌ Erro de Execução: {e}")


if __name__ == "__main__":
    inspect_contracts()
