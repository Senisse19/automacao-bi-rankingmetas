import json
from dotenv import load_dotenv

load_dotenv()
from core.clients.powerbi_client import PowerBIClient


def extract_schema():
    client = PowerBIClient()
    if not client.authenticate():
        print("Falha na autenticação.")
        return

    # Querying the columns and tables from Analysis Services
    print("Consultando $SYSTEM.TMSCHEMA_TABLES...")
    tables = client.execute_dax("SELECT [ID], [Name] FROM $SYSTEM.TMSCHEMA_TABLES")

    print("Consultando $SYSTEM.TMSCHEMA_COLUMNS...")
    columns = client.execute_dax("SELECT [TableID], [ExplicitName] FROM $SYSTEM.TMSCHEMA_COLUMNS")

    if not tables or not columns:
        print("Falha ao obter schema.")
        return

    # Map tables
    table_map = {t.get("[ID]"): t.get("[Name]") for t in tables}

    # Group columns
    schema = {}
    for col in columns:
        tid = col.get("[TableID]")
        cname = col.get("[ExplicitName]")
        tname = table_map.get(tid, f"Unknown_{tid}")

        if tname not in schema:
            schema[tname] = []
        schema[tname].append(cname)

    with open("pbi_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print("Schema salvo em pbi_schema.json")


if __name__ == "__main__":
    extract_schema()
