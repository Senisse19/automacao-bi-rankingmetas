import requests
import os
from dotenv import load_dotenv

# Load env
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
load_dotenv(os.path.join(project_root, ".env"))

logger = None


class SimplePowerBI:
    def __init__(self, workspace_id=None, dataset_id=None):
        self.tenant = os.environ.get("SHAREPOINT_TENANT")
        self.client_id = os.environ.get("POWERBI_CLIENT_ID") or os.environ.get("SHAREPOINT_CLIENT_ID")
        self.client_secret = os.environ.get("POWERBI_CLIENT_SECRET") or os.environ.get("SHAREPOINT_CLIENT_SECRET")
        self.tenant_id = os.environ.get("POWERBI_TENANT_ID") or os.environ.get("SHAREPOINT_TENANT")

        self.workspace_id = workspace_id or os.environ.get("POWERBI_WORKSPACE_ID")
        self.dataset_id = dataset_id or "ae481f4d-b8df-4e0c-915e-47a4606bec06"

        self.token = None
        self.session = requests.Session()

    def authenticate(self) -> bool:
        if not self.tenant_id:
            print("Missing Tenant ID")
            return False

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default",
        }

        try:
            resp = self.session.post(token_url, data=data)
            resp.raise_for_status()
            self.token = resp.json().get("access_token")
            return True
        except Exception as e:
            print(f"Auth Error: {e}")
            return False

    def execute_dax(self, query):
        if not self.token:
            self.authenticate()

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "queries": [{"query": query}],
            "serializerSettings": {"includeNulls": True},
        }

        resp = self.session.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            print(f"Error ({resp.status_code}): {resp.text}")
            return None

        try:
            return resp.json()["results"][0]["tables"][0]["rows"]
        except:
            return []


def run():
    client = SimplePowerBI()
    print("--- PROBING SCHEMA (DMV) ---")

    # Check Columns
    print("\n[COLUMNS SEARCH]")
    q_cols = """
    SELECT [Name], [ExplicitName], [Description] FROM $SYSTEM.TMSCHEMA_COLUMNS
    WHERE [TableID] IN (SELECT [ID] FROM $SYSTEM.TMSCHEMA_TABLES WHERE [Name] = 'Competencia')
    AND (
        [Name] LIKE '%nome%' OR 
        [Name] LIKE '%razao%' OR 
        [Name] LIKE '%cliente%' OR 
        [Name] LIKE '%atraso%' OR
        [Name] LIKE '%dias%'
    )
    """
    rows = client.execute_dax(q_cols)
    if rows:
        for r in rows:
            print(f"Col: {r.get('Name')} | Explicit: {r.get('ExplicitName')}")
    else:
        print("No columns found matching criteria.")

    # Check Measures
    print("\n[MEASURES SEARCH]")
    q_meas = """
    SELECT [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES
    WHERE (
        [Name] LIKE '%Dias%' OR 
        [Name] LIKE '%Atraso%' OR
        [Expression] LIKE '%Dias%'
    )
    """
    rows_m = client.execute_dax(q_meas)
    if rows_m:
        for r in rows_m:
            print(f"Measure: {r.get('Name')}")
            # Print expression snippet if possible
            expr = r.get("Expression", "")[:100].replace("\n", " ")
            print(f"  Expr: {expr}...")


if __name__ == "__main__":
    run()
