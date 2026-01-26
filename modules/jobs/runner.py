import sys
import os

# Ensure root directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("run_jobs")

def transform_job(item):
    """Maps Data Lake item to Nexus Jobs schema."""
    # id, job, data_cadastro, data_inicio_contrato, data_cancelamento, 
    # cliente_id, unidade_id, franqueado_id, modelo_negocio, raw_data
    
    return {
        "id": item.get("codigo"),
        "job": item.get("job"),
        "data_cadastro": item.get("data_cadastro"),
        "data_inicio_contrato": item.get("data_inicio_contrato"),
        "data_cancelamento": item.get("data_cancelamento"),
        "cliente_id": item.get("codigo_cliente"),
        "unidade_id": item.get("codigo_unidade"),
        "franqueado_id": item.get("codigo_franqueado"),
        "modelo_negocio": item.get("modelo_negocio"),
        
        # Extended Columns
        "codigo_produto": item.get("codigo_produto"),
        "codigo_checklist": item.get("codigo_checklist"),
        "job_divisao": item.get("job_divisao"),
        "data_entrega": item.get("data_entrega"),
        "prazo_ata": item.get("prazo_ata"),
        "ano_analise_inicial": item.get("ano_analise_inicial"),
        "ano_analise_final": item.get("ano_analise_final"),
        "percentual": item.get("percentual"),
        "percentual_passivo": item.get("percentual_passivo"),
        "motivo_cancelamento": item.get("motivo_cancelamento"),
        "user_cancelamento": item.get("user_cancelamento"),
        "responsavel_comercial": item.get("responsavel_comercial"),
        "responsavel_venda": item.get("responsavel_venda"),
        "user_add": item.get("user_add"),
        "data_recebimento": item.get("data_recebimento"),
        "cnpj": item.get("cnpj"),
        "linha": item.get("linha"),
        "codigo_qualidade": item.get("codigo_qualidade")
    }

def run():
    client = JobsClient()
    svc = SupabaseService()
    
    logger.info("--- Starting Jobs Sync ---")
    
    try:
        items = client.fetch_all_jobs()
        logger.info(f"Fetched {len(items)} jobs from Data Lake.")
        
        if not items:
            logger.warning("No items to sync.")
            return

        # Transform
        logger.info("Transforming data...")
        transformed = []
        for i in items:
            if i.get("codigo"):
                transformed.append(transform_job(i))
        
        logger.info(f"Prepared {len(transformed)} items for upsert.")

        # Batch Upsert
        BATCH_SIZE = 500
        for i in range(0, len(transformed), BATCH_SIZE):
            batch = transformed[i:i+BATCH_SIZE]
            logger.info(f"Upserting batch {i} to {i+len(batch)}...")
            svc.upsert_data("nexus_jobs", batch)
            
        logger.info("Jobs Sync Completed Successfully!")
    except Exception as e:
        logger.error(f"Critical error in Jobs Sync: {e}")

if __name__ == "__main__":
    run()
