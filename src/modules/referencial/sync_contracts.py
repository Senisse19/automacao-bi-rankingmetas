from datetime import datetime

from src.core.clients.jobs_client import JobsClient
from src.core.services.supabase_service import SupabaseService
from src.core.utils.logger import get_logger

logger = get_logger("sync_contracts")


class SyncContracts:
    def __init__(self):
        self.db = SupabaseService()
        self.client = JobsClient()
        self.table_name = "nexus_contratos_recorrentes"

    def run(self, days_ago=30, full_load=False):
        logger.info(f"Starting {self.table_name} sync (full_load={full_load})...")

        endpoint = "/contratos_recorrentes/"  # IMPORTANTE: Trailing slash

        try:
            # Buscar contratos. Se full_load=True, pega tudo. Se não, filtra por data (SE A API SUPORTAR).
            # Como não conhecemos filtros de data, vamos assumir carga completa por seguranca
            # ou limitar se for muito grande.
            # O endpoint parece suportar paginação padrão do DataTables ou similar.

            # TODO: Implementar filtro por data_alteracao se a API suportar para otimizar.
            # Por enquanto, fetch_all simples.

            all_contracts = self.client.fetch_all(endpoint)
            logger.info(f"Fetched {len(all_contracts)} contracts from API")

            if not all_contracts:
                return

            upsert_data = []
            # Batch upsert para não estourar payload
            BATCH_SIZE = 1000

            for item in all_contracts:
                upsert_data.append(
                    {
                        "codigo": item.get("codigo"),
                        "tipo_contrato": item.get("tipo_contrato"),
                        "participante": item.get("participante"),
                        "data_cadastro": item.get("data_cadastro"),
                        "ativo_int": item.get("ativo_int"),
                        "data_assinatura": item.get("data_assinatura"),
                        "fim_contrato": item.get("fim_contrato"),
                        "regime_tributacao": item.get("regime_tributacao"),
                        "valor_a_vista": item.get("valor_a_vista"),
                        "mensalidade": item.get("mensalidade"),
                        "observacao": item.get("observacao"),
                        "status": "Ativo" if item.get("ativo_int") == 1 else "Inativo",  # Exemplo de derivacao
                        "updated_at": datetime.now().isoformat(),
                    }
                )

                if len(upsert_data) >= BATCH_SIZE:
                    self.db.upsert_data(self.table_name, upsert_data, on_conflict="codigo")
                    logger.info(f"Upserted batch of {len(upsert_data)}")
                    upsert_data = []

            # Upsert remanescentes
            if upsert_data:
                self.db.upsert_data(self.table_name, upsert_data, on_conflict="codigo")
                logger.info(f"Upserted final batch of {len(upsert_data)}")

        except Exception as e:
            logger.error(f"Error syncing contracts: {e}")
            raise
