import os
import sys

# Configurar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Importar módulo e dependências
import modules.jobs.automation as automation_module
from modules.jobs.automation import JobsAutomation
from utils.logger import get_logger

logger = get_logger("local_gen")

# 1. Definir diretório de saída
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tests/output/jobs"))
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# 2. Monkeypatch: Redirecionar IMAGES_DIR para nosso output de teste
print(f"📂 Redirecionando saída para: {OUTPUT_DIR}")
automation_module.IMAGES_DIR = OUTPUT_DIR


# 3. Subclasse para inibir envio
class LocalGenerator(JobsAutomation):
    def _send_report(self, title, path, recipients, template):
        """Não envia nada, apenas loga que o arquivo está pronto."""
        logger.info(f"✅ RELATÓRIO GERADO: {title}")
        logger.info(f"   -> Caminho: {path}")


if __name__ == "__main__":
    print("\n🎨 GERADOR DE RELATÓRIOS LOCAIS (LAYOUT TEST) 🎨")

    # Destinatário Mock (necessário para passar na lógica de verificação de tags)
    mock_recipient = {
        "name": "Dev Tester",
        "phone": "00000000",
        "tags": ["jobs_all", "tax", "corporate"],  # Garante geração de TODOS os tipos
    }

    # Data de teste inicial (D-1 de 19/02/2026)
    target_date = "2026-02-18"

    try:
        runner = LocalGenerator()

        # Lógica de Fallback: Verificar se há jobs na data alvo
        print(f"🔍 Verificando jobs para {target_date}...")
        new_jobs, cnc_jobs = runner.fetch_jobs(target_date, target_date)

        if not new_jobs and not cnc_jobs:
            print(f"⚠️ Nenhum job encontrado para {target_date}. Buscando última data disponível...")
            # Buscar última data de cadastro no banco
            resp = runner.supabase._get(
                "nexus_jobs",
                {"select": "data_cadastro", "order": "data_cadastro.desc", "limit": 1},
            )
            if resp:
                last_date_full = resp[0].get("data_cadastro")
                target_date = last_date_full.split("T")[0]
                print(f"📅 Última data encontrada no banco: {target_date}")
            else:
                print("❌ Nenhum job encontrado no banco de dados.")

        logger.info(f"Gerando documentos para data base: {target_date}...")

        runner.process_reports(
            daily=True,
            weekly=False,
            recipients=[mock_recipient],
            date_override=target_date,
        )

        print("\n✨ GERAÇÃO CONCLUÍDA ✨")
        print(f"Verifique os arquivos em: {OUTPUT_DIR}")
        os.system(f'explorer "{OUTPUT_DIR}"')

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()
