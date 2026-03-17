import os

try:
    from dotenv import load_dotenv

    current_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(current_dir, ".env")
    load_dotenv(dotenv_path)
except ImportError:
    pass

from src.core.clients.powerbi_client import PowerBIClient


def main():
    output_file = "datasets_found.txt"
    try:
        client = PowerBIClient()
        datasets = client.list_datasets()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Workspace: {client.workspace_id}\n")
            f.write(f"Encontrados {len(datasets)} datasets\n\n")
            for ds in datasets:
                f.write(f"- {ds['name']} | ID: {ds['id']}\n")
        print(f"Sucesso! Resultados salvos em {output_file}")
    except Exception as e:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}")
        print(f"Erro salvo em {output_file}")


if __name__ == "__main__":
    main()
