"""
Script de sincronização: Datalake Nexus -> Supabase (nexus_contas_receber)
Executado todo dia na madrugada para manter o espelho atualizado.
"""

import sys
import os
from datetime import datetime

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("sync_contas_receber")

# Campos da API que serão mapeados para a tabela no Supabase
FIELD_MAP = {
    "id": "id",
    "codigo": "codigo",
    "razao_social": "razao_social",
    "bandeira": "bandeira",
    "descricao": "descricao",
    "data_emissao": "data_emissao",
    "data_vencimento": "data_vencimento",
    "valor_contas_receber": "valor",
    "personalizar": "personalizar",
}


def sync_contas_receber():
    """Busca todos os registros do datalake e faz upsert no Supabase."""
    logger.info("=== SYNC Contas a Receber ===")

    client = UnidadesClient()
    svc = SupabaseService()

    # Busca todos os registros paginando pela API do datalake
    logger.info("Buscando dados da API Nexus (contas-receber)...")
    data = client.fetch_all_from_source("contas-receber")
    logger.info(f"Total de registros obtidos: {len(data)}")

    if not data:
        logger.warning("Nenhum dado retornado da API. Sync abortado.")
        return

    # Mapeia os campos para o schema da tabela
    agora = datetime.now().isoformat()
    batch = []

    for item in data:
        row = {col_dest: item.get(col_src) for col_src, col_dest in FIELD_MAP.items()}
        row["updated_at"] = agora
        batch.append(row)

    # Realiza upsert em lotes de 500
    chunk_size = 500
    total_chunks = (len(batch) + chunk_size - 1) // chunk_size

    for i in range(0, len(batch), chunk_size):
        chunk = batch[i : i + chunk_size]
        chunk_num = (i // chunk_size) + 1
        success = svc.upsert_data("nexus_contas_receber", chunk)
        if success:
            logger.info(f"Chunk {chunk_num}/{total_chunks} upsertado ({len(chunk)} registros)")
        else:
            logger.error(f"Falha no chunk {chunk_num}/{total_chunks}")

    logger.info(f"=== SYNC concluído: {len(batch)} registros processados ===")


if __name__ == "__main__":
    sync_contas_receber()
