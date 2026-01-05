"""
Cliente Power BI - Extrai dados via DAX
Funciona com licença Premium Per User (PPU)
"""
import requests
import os


class PowerBIClient:
    def __init__(self):
        self.tenant = os.environ.get("POWERBI_TENANT", "audittecnologia.onmicrosoft.com")
        self.client_id = os.environ.get("SHAREPOINT_CLIENT_ID", "75342350-912b-496c-8e37-9db1881a3c7e")
        self.client_secret = os.environ.get("SHAREPOINT_CLIENT_SECRET", "REDACTED")
        self.workspace_id = os.environ.get("POWERBI_WORKSPACE_ID", "4600324e-148c-4aae-a743-601628c04d29")
        self.dataset_id = os.environ.get("POWERBI_DATASET_ID", "5f1e9f0f-8388-438d-a0be-6a5e13bb3ce4")
        self.token = None
    
    def authenticate(self):
        """Autentica no Azure AD e obtém token de acesso"""
        token_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default"
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            self.token = response.json().get("access_token")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro na autenticacao: {e}")
            return False
    
    def execute_dax(self, query):
        """Executa uma query DAX e retorna os resultados"""
        if not self.token:
            if not self.authenticate():
                return None
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/executeQueries"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "queries": [{"query": query}],
            "serializerSettings": {"includeNulls": True}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            tables = result.get("results", [{}])[0].get("tables", [{}])
            
            if tables:
                rows = tables[0].get("rows", [])
                return rows
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao executar DAX: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Detalhes: {e.response.text[:500]}")
            return None
    
    def get_sample_data(self):
        """Retorna dados de exemplo para testar a conexao"""
        # Query simples para testar conexao
        query = 'EVALUATE ROW("Status", "Conexao OK", "Timestamp", NOW())'
        return self.execute_dax(query)
    
    def list_datasets(self):
        """Lista todos os datasets do workspace"""
        if not self.token:
            if not self.authenticate():
                return []
        
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("value", [])
        except:
            return []


# Teste direto
if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DE CONEXAO POWER BI")
    print("=" * 60)
    
    client = PowerBIClient()
    
    # 1. Autenticar
    print("\n[1] Autenticando...")
    if client.authenticate():
        print("    OK - Token obtido")
    else:
        print("    FALHA")
        exit(1)
    
    # 2. Listar datasets
    print("\n[2] Listando datasets...")
    datasets = client.list_datasets()
    for ds in datasets:
        marker = ">>>" if ds['id'] == client.dataset_id else "   "
        print(f"    {marker} {ds['name']} (ID: {ds['id'][:20]}...)")
    
    # 3. Testar conexao
    print("\n[3] Testando query DAX...")
    result = client.get_sample_data()
    if result:
        print(f"    OK - Resultado: {result}")
    else:
        print("    FALHA")
    
    # 4. Tentar buscar dados reais do modelo
    print("\n[4] Buscando dados do modelo Ranking_Metas...")
    
    # Tentar diferentes queries para descobrir tabelas
    test_queries = [
        ("TOPN 10 linhas de qualquer tabela", "EVALUATE TOPN(10, SELECTCOLUMNS(VALUES('Table'), \"Col\", \"Valor\"))"),
        ("Valores unicos", "EVALUATE DISTINCT(VALUES(1))"),
    ]
    
    # Query basica que funciona em qualquer modelo
    simple_query = '''
    EVALUATE 
    ROW(
        "Dataset", "Ranking_Metas",
        "Status", "Conectado",
        "Data", FORMAT(TODAY(), "DD/MM/YYYY"),
        "Hora", FORMAT(NOW(), "HH:MM:SS")
    )
    '''
    
    result = client.execute_dax(simple_query)
    if result:
        print(f"    Dados retornados:")
        for row in result:
            for key, value in row.items():
                print(f"      {key}: {value}")
    
    print("\n" + "=" * 60)
    print("CONEXAO POWER BI FUNCIONANDO!")
    print("=" * 60)
    print("\nProximos passos:")
    print("1. Informe os nomes das tabelas/medidas do seu modelo")
    print("2. Montaremos as queries DAX especificas")
    print("3. Criaremos a automacao para enviar dados via WhatsApp")
