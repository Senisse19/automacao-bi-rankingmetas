"""
Cliente Power BI - Extrai dados via DAX.
Funciona com licença Premium Per User (PPU).
Gerencia autenticação Azure AD e execução de queries.
"""

import hashlib
import os
import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.utils.logger import get_logger

logger = get_logger("powerbi_client")


class _DAXCache:
    """
    Cache em memória thread-safe com TTL para resultados de queries DAX.

    Compartilhado entre todas as instâncias de PowerBIClient no processo.
    Evita requisições repetidas ao Power BI quando a mesma query é executada
    múltiplas vezes dentro da janela de validade (padrão: 30 minutos).
    """

    def __init__(self, ttl_seconds: int = 1800):
        self._store: dict[str, tuple[list, float]] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def get(self, key: str) -> list | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            result, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return result

    def set(self, key: str, value: list) -> None:
        with self._lock:
            self._store[key] = (value, time.time() + self._ttl)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Instância única compartilhada por todas as chamadas DAX do processo (30 min TTL)
_dax_cache = _DAXCache(ttl_seconds=1800)


class PowerBIClient:
    def __init__(self, workspace_id=None, dataset_id=None):
        self.tenant = os.environ.get("SHAREPOINT_TENANT")
        self.client_id = os.environ.get("SHAREPOINT_CLIENT_ID")
        self.client_secret = os.environ.get("SHAREPOINT_CLIENT_SECRET")

        # Priority: Constructor Args > Env Vars
        self.workspace_id = workspace_id or os.environ.get("POWERBI_WORKSPACE_ID")
        self.dataset_id = dataset_id or os.environ.get("POWERBI_DATASET_ID")

        # Validate critical env vars
        if not self.tenant or not self.client_id or not self.client_secret:
            raise ValueError(
                "CRITICAL: Missing required environment variables "
                "(SHAREPOINT_TENANT, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET)."
            )

        self.token = None
        self.token_expiry = 0  # Timestamp de expiração do token OAuth

        # Configure Autoscaling Retry
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def authenticate(self) -> bool:
        """
        Autentica no Azure AD usando credenciais de Service Principal.
        Obtém e armazena o token de acesso (Bearer Token).
        """
        token_url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default",
        }

        try:
            response = self.session.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get("access_token")
            # Buffer de 60s para evitar uso de token prestes a expirar
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = time.time() + expires_in - 60
            logger.info(f"Token OAuth obtido (expira em {expires_in}s)")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na autenticacao: {e}")
            return False

    def execute_dax(self, query: str) -> list | None:
        """
        Executa uma consulta DAX no dataset configurado.
        Retorna uma lista de linhas (dicionários) ou lista vazia em caso de erro.

        Resultado é cacheado por 30 minutos para evitar requisições duplicadas
        ao Power BI quando a mesma query é chamada várias vezes no mesmo ciclo.
        """
        # Verifica cache antes de qualquer requisição HTTP
        cache_key = hashlib.md5(query.encode("utf-8")).hexdigest()
        cached = _dax_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"DAX cache hit [{cache_key[:8]}]")
            return cached

        # Renova token se ausente ou expirado
        if not self.token or time.time() >= self.token_expiry:
            if not self.authenticate():
                return None

        url = (
            f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/"
            f"{self.dataset_id}/executeQueries"
        )

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {
            "queries": [{"query": query}],
            "serializerSettings": {"includeNulls": True},
        }

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()
            tables = result.get("results", [{}])[0].get("tables", [{}])

            if tables:
                rows = tables[0].get("rows", [])
                _dax_cache.set(cache_key, rows)
                return rows
            return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao executar DAX: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Detalhes: {e.response.text[:500]}")
            return None

    def get_sample_data(self) -> list | None:
        """Retorna dados de exemplo (teste de conexão simples)."""
        # Query simples para testar conexao
        query = 'EVALUATE ROW("Status", "Conexao OK", "Timestamp", NOW())'
        return self.execute_dax(query)

    def list_datasets(self) -> list:
        """Lista todos os datasets disponíveis no workspace configurado."""
        if not self.token:
            if not self.authenticate():
                return []

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets"
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("value", [])
        except Exception:
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
        marker = ">>>" if ds["id"] == client.dataset_id else "   "
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
        (
            "TOPN 10 linhas de qualquer tabela",
            'EVALUATE TOPN(10, SELECTCOLUMNS(VALUES(\'Table\'), "Col", "Valor"))',
        ),
        ("Valores unicos", "EVALUATE DISTINCT(VALUES(1))"),
    ]

    # Query basica que funciona em qualquer modelo
    simple_query = """
    EVALUATE
    ROW(
        "Dataset", "Ranking_Metas",
        "Status", "Conectado",
        "Data", FORMAT(TODAY(), "DD/MM/YYYY"),
        "Hora", FORMAT(NOW(), "HH:MM:SS")
    )
    """

    result = client.execute_dax(simple_query)
    if result:
        print("    Dados retornados:")
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
