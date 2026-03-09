from datetime import datetime

from core.clients.jobs_client import JobsClient
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

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

            # Transformar dados para formato do banco
            upsert_data = []
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

            # Upsert
            self.db.upsert_data(self.table_name, upsert_data, on_conflict="codigo")
            logger.info(f"Upserted {len(upsert_data)} records into {self.table_name}")

        except Exception as e:
            logger.error(f"Error syncing services: {e}")
            raise
