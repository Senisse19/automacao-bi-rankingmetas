import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from utils.logger import get_logger

logger = get_logger("inspect_job")


def inspect():
    client = JobsClient()
    # Job ID de exemplo: 29685

    url = f"{client.api_url}/jobs/29685"
    print(f"Buscando job de exemplo: {url}")

    try:
        # Tenta endpoint de detalhe primeiro
        resp = client.session.get(url, headers=client.headers)
        if resp.status_code == 200:
            data = resp.json()
            output_file = "tests/output/job_inspection.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"JSON salvo em: {output_file}")
            return

        # Se falhar, tenta listar e pegar o primeiro
        print("Endpoint de detalhe falhou, tentando listagem...")
        url_list = f"{client.api_url}/jobs/"
        resp = client.session.get(url_list, headers=client.headers, params={"limit": 1})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                item = data["results"][0]
            elif isinstance(data, list):
                item = data[0]
            else:
                item = data

            output_file = "tests/output/job_inspection.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(item, f, indent=4, ensure_ascii=False)
            print(f"JSON salvo em: {output_file}")

    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    inspect()
