from datetime import datetime

from src.core.clients.jobs_client import JobsClient
from src.core.services.supabase_service import SupabaseService
from src.core.utils.logger import get_logger

logger = get_logger("sync_services")


class SyncServices:
    def __init__(self):
        self.db = SupabaseService()
        self.client = JobsClient()
        self.table_name = "nexus_servicos"

    def run(self):
        logger.info(f"Starting {self.table_name} sync...")

        try:
            # Buscar todos os serviços (sem paginação pesada geralmente)
            all_services = self.client.fetch_all("/servicos")

            logger.info(f"Fetched {len(all_services)} services from API")

            if not all_services:
                return

            upsert_data = []
            BATCH_SIZE = 1000

            for item in all_services:
                upsert_data.append(
                    {
                        "codigo": item.get("codigo"),
                        "nome": item.get("nome"),
                        "sigla": item.get("sigla"),
                        "modelo": item.get("modelo"),
                        "sub_produto": item.get("sub_produto"),
                        "ativo": item.get("ativo"),
                        "updated_at": datetime.now().isoformat(),
                    }
                )

                if len(upsert_data) >= BATCH_SIZE:
                    self.db.upsert_data(self.table_name, upsert_data, on_conflict="codigo")
                    logger.info(f"Upserted batch of {len(upsert_data)}")
                    upsert_data = []

            if upsert_data:
                self.db.upsert_data(self.table_name, upsert_data, on_conflict="codigo")
                logger.info(f"Upserted final batch of {len(upsert_data)} records into {self.table_name}")

        except Exception as e:
            logger.error(f"Error syncing services: {e}")
            raise
