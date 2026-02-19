import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from modules.referencial.sync_services import SyncServices
from modules.referencial.sync_contracts import SyncContracts
from utils.logger import get_logger

logger = get_logger("backfill_enrichment")


def run_backfill():
    logger.info("Starting enrichment tables backfill...")

    try:
        logger.info("1. Syncing Services...")
        SyncServices().run()

        logger.info("2. Syncing Contracts...")
        SyncContracts().run(full_load=True)  # Assumindo carga completa no init

        logger.info("✅ Backfill complete.")
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        raise


if __name__ == "__main__":
    run_backfill()
