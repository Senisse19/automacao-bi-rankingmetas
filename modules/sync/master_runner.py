import sys
import os
import time
from datetime import datetime

# Garantir que o diretório raiz está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from utils.logger import get_logger
from core.services.supabase_service import SupabaseService

# Importar Runners dos Módulos
from modules.jobs import runner as jobs_runner
from modules.sync import nexus_runner

logger = get_logger("master_sync")


def run():
    """
    Executa o processo de Sincronização Mestre:
    1. Jobs (Incremental)
    2. Dados Base do Nexus (Unidades, Participantes, Modelos)
    """
    start_time = time.time()
    logger.info("🚀 INICIANDO SINCRONIZAÇÃO MESTRE DIÁRIA 🚀")

    svc = SupabaseService()

    # 1. Sincronizar Jobs
    try:
        logger.info("[1/2] Executando Sincronização de Jobs...")
        jobs_runner.run()
        logger.info("✅ Sincronização de Jobs Concluída.")
    except Exception as e:
        logger.error(f"❌ Falha na Sincronização de Jobs: {e}")

    # 2. Sincronizar Dados Base do Nexus
    try:
        logger.info("[2/2] Executando Sincronização de Referências Nexus (Unidades, Modelos, Participantes)...")
        nexus_runner.run()
        logger.info("✅ Sincronização Nexus Concluída.")
    except Exception as e:
        logger.error(f"❌ Falha na Sincronização Nexus: {e}")

    elapsed = time.time() - start_time
    logger.info(f"🏁 SINCRONIZAÇÃO MESTRE FINALIZADA em {elapsed:.2f} segundos. 🏁")

    # Opcional: Registrar conclusão nos logs de automação do Supabase
    try:
        svc.log_event(
            "master_sync_completed",
            {"duration": elapsed, "timestamp": datetime.now().isoformat()},
        )
    except Exception:
        pass


if __name__ == "__main__":
    run()
