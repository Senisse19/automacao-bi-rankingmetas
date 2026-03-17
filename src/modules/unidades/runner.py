"""
Automação de Unidades (Power BI)
Extrai dados de unidades do Power BI e envia relatórios (Diários/Semanais).
"""

import argparse
import json
from datetime import datetime, timedelta

from jinja2 import Template

from src.config import POWERBI_CONFIG
from src.core.clients.evolution_client import EvolutionClient
from src.core.clients.powerbi_client import PowerBIClient
from src.core.services.image_renderer.unidades_renderer import UnidadesRenderer
from src.core.services.notification_service import NotificationService
from src.core.services.supabase_service import SupabaseService
from src.core.utils.greeting import get_saudacao
from src.core.utils.logger import get_logger

from .data_fetcher import PowerBIUnidadesFetcher

logger = get_logger("unidades_automation")


class UnidadesAutomation:
    """
    Controlador principal da automação de Unidades.
    """

    def __init__(self):
        dataset_id = POWERBI_CONFIG.get("unidades_dataset_id")
        workspace_id = POWERBI_CONFIG.get("unidades_workspace_id")

        if not dataset_id or not workspace_id:
            logger.error("Dataset ID ou Workspace ID de Unidades não configurado.")
            # Fallback para o dataset id geral se necessário, ou erro
            raise ValueError("Configurações de Power BI para Unidades ausentes.")

        self.powerbi = PowerBIClient(workspace_id=workspace_id, dataset_id=dataset_id)
        self.fetcher = PowerBIUnidadesFetcher(self.powerbi)
        self.renderer = UnidadesRenderer()
        self.whatsapp = EvolutionClient()
        self.supabase = SupabaseService()
        self.notification_service = NotificationService(self.supabase)

    def get_dates(self, report_type="daily"):
        """Retorna as datas de início e fim baseadas no tipo de relatório."""
        now = datetime.now()
        if report_type == "daily":
            # Ontem
            date_end = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            date_start = date_end
        else:
            # Semana passada (Segunda a Domingo)
            days_to_last_monday = now.weekday() + 7
            monday = now - timedelta(days=days_to_last_monday)
            sunday = monday + timedelta(days=6)
            date_start = monday.strftime("%Y-%m-%d")
            date_end = sunday.strftime("%Y-%m-%d")

        return date_start, date_end

    def fetch_dashboard_data(self, date_start, date_end):
        """Busca todos os dados necessários para o dashboard de unidades."""
        logger.info(f"Buscando dados de unidades de {date_start} até {date_end}")

        summary = self.fetcher.fetch_summary(date_start, date_end)
        new_units = self.fetcher.fetch_units_list(date_start, date_end, status="Nova")
        inactive_units = self.fetcher.fetch_units_list(date_start, date_end, status="Inativada")

        return {"summary": summary, "new_units_list": new_units, "inactive_units_list": inactive_units}

    def run(self, report_type="daily", generate_only=False, recipients=None, template_content=None, dry_run=False):
        """Executa o ciclo completo da automação."""
        logger.info(f"Iniciando automação de Unidades ({report_type})...")

        date_start, date_end = self.get_dates(report_type)

        # 1. Fetch Data
        data = self.fetch_dashboard_data(date_start, date_end)

        # 2. Render Image
        # Adaptando os dados para o formato esperado pelo UnidadesRenderer
        # O renderer espera 'new', 'cancelled' e 'upsell'
        render_data = {
            "date": date_end,
            "start_date": date_start,
            "new": data["new_units_list"],
            "cancelled": data["inactive_units_list"],
            "upsell": [],  # TODO: Verificar se upsell deve ser incluído
            "summary": data["summary"],
        }

        output_path = self.renderer.generate_unidades_reports(
            render_data, report_type="weekly" if report_type == "weekly" else "daily"
        )

        logger.info(f"Relatório gerado em: {output_path}")

        # 3. Send
        if not generate_only:
            if not recipients:
                logger.error("Nenhum destinatário fornecido para envio de Unidades.")
                return output_path

            logger.info(f"Enviando para {len(recipients)} destinatários...")

            # Monta o lote de envios
            saudacao = get_saudacao()
            data_fmt = datetime.strptime(date_end, "%Y-%m-%d").strftime("%d/%m/%Y")
            data_inicio_fmt = datetime.strptime(date_start, "%Y-%m-%d").strftime("%d/%m/%Y")
            msg_tipo = "Diário" if report_type == "daily" else "Semanal"

            batch = []
            for r in recipients:
                nome = r.get("nome") or r.get("name") or "Colaborador"
                primeiro_nome = nome.split()[0].title()

                context = {
                    "nome": primeiro_nome,
                    "nome_completo": nome,
                    "saudacao": saudacao,
                    "saudacao_lower": saudacao.lower(),
                    "data": data_fmt,
                    "data_inicio": data_inicio_fmt,
                    "tipo": msg_tipo,
                    "titulo": f"Relatório de Unidades {msg_tipo} — {data_fmt}",
                }

                if template_content:
                    try:
                        if "{{" in template_content:
                            caption = Template(template_content).render(**context)
                        else:
                            caption = template_content.format(**context)
                    except Exception as e:
                        logger.error(f"Erro ao formatar template para {nome}: {e}")
                        caption = f"{saudacao}, {primeiro_nome}!\n\n📋 Relatório de Unidades {msg_tipo} — {data_fmt}"
                else:
                    caption = f"{saudacao}, {primeiro_nome}!\n\n📋 Relatório de Unidades {msg_tipo} — {data_fmt}"

                batch.append((r, output_path, caption))

            if not dry_run:
                self.notification_service.send_batch(batch, context_tag="unidades")
            else:
                logger.info(f"[DRY-RUN] Simulação de envio para {len(batch)} contatos.")

        return output_path


def main():
    parser = argparse.ArgumentParser(description="Automação de Unidades Power BI")
    parser.add_argument(
        "--type", choices=["daily", "weekly"], default="daily", help="Tipo de relatório (daily ou weekly)"
    )
    parser.add_argument("--generate-only", action="store_true", help="Apenas gerar a imagem, sem enviar")
    parser.add_argument("--dry-run", action="store_true", help="Simular envio (apenas logs)")
    parser.add_argument("--payload", type=str, help="JSON payload com destinatários e template")

    args = parser.parse_args()

    automation = UnidadesAutomation()

    recipients = None
    template_content = None

    if args.payload:
        try:
            data = json.loads(args.payload)
            recipients = data.get("recipients")
            template_content = data.get("template_content")
            logger.info(f"Recebido payload via CLI com {len(recipients) if recipients else 0} destinatários.")
        except Exception as e:
            logger.error(f"Erro ao fazer parse do payload JSON: {e}")
            return

    automation.run(
        report_type=args.type,
        generate_only=args.generate_only,
        recipients=recipients,
        template_content=template_content,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
