import os
import sys

# Adicionar root ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from modules.jobs.automation import JobsAutomation
from utils.logger import get_logger

logger = get_logger("dry_run")


class DryRunJobsAutomation(JobsAutomation):
    def _send_report(self, title, path, recipients, template):
        """Override para NÃO enviar mensagem real."""
        logger.info(f"⚡ [DRY RUN] WOULD SEND '{title}'")
        logger.info(f"   -> File: {path}")
        logger.info(f"   -> TO: {[r['name'] for r in recipients]}")


if __name__ == "__main__":
    print("\n🚀 INICIANDO DRY RUN DA AUTOMAÇÃO DE JOBS 🚀")

    # Simular destinatários (Victor Senisse com todas as tags)
    mock_recipients = [
        {
            "name": "Victor Senisse (Admin)",
            "phone": "5551998129077",
            "tags": ["tax", "corporate", "director"],
        },
        {"name": "Usuario Tax", "phone": "0000", "tags": ["tax"]},
        {"name": "Usuario Corp", "phone": "1111", "tags": ["corporate"]},
    ]

    # Data com dados conhecidos: 2020-10-02
    target_date = "2020-10-02"

    runner = DryRunJobsAutomation()

    logger.info(f"Simulando execução para data: {target_date}")

    print("DEBUG: Calling process_reports...")
    try:
        runner.process_reports(
            daily=True,
            weekly=False,
            recipients=mock_recipients,
            date_override=target_date,
        )
        print("DEBUG: process_reports returned.")
    except KeyboardInterrupt:
        print("\nDEBUG: Interrupted by user/system.")
    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ DRY RUN FINALIZADO.")
