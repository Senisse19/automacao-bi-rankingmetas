"""
Automação Painel INA
Responsável por extrair dados do Painel INA e enviar resumo via WhatsApp.
Inclui funcionalidade de autodescoberta de schema.
"""

import os
import sys
from datetime import datetime

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from core.clients.powerbi_client import PowerBIClient
from core.services.supabase_service import SupabaseService
from core.clients.evolution_client import EvolutionClient
from utils.logger import get_logger
from core.services.image_renderer.ina_renderer import InaRenderer
from config import POWERBI_CONFIG

logger = get_logger("run_ina")

# IDs lidos da configuração centralizada (variáveis POWERBI_INA_*)
INA_DATASET_ID = POWERBI_CONFIG.get("ina_dataset_id")
INA_WORKSPACE_ID = POWERBI_CONFIG.get("ina_workspace_id")


class InaAutomation:
    def __init__(self):
        # Validação para garantir que as variáveis estão configuradas antes de iniciar
        if not INA_DATASET_ID or not INA_WORKSPACE_ID:
            raise ValueError(
                "❌ Variáveis POWERBI_INA_DATASET_ID e POWERBI_WORKSPACE_ID não configuradas. "
                "Configure-as no Coolify antes de executar a automação INA."
            )
        logger.info(f"🔌 Conectando ao Power BI - Workspace: {INA_WORKSPACE_ID} | Dataset: {INA_DATASET_ID}")
        self.powerbi = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)
        self.whatsapp = EvolutionClient()
        self.supabase = SupabaseService()

    def discover_schema(self):
        """
        Executa queries nas DMVs (Dynamic Management Views) para descobrir tabelas e medidas.
        """
        logger.info("🕵️ Iniciando descoberta de schema do Painel INA...")
        q_simple = 'EVALUATE ROW("Status", "Conectado", "Hora", NOW())'
        try:
            result = self.powerbi.execute_dax(q_simple)
            if result:
                logger.info(f"✅ Conectividade OK: {result}")
        except Exception as e:
            logger.error(f"Erro ao testar conectividade: {e}")

    def fetch_kpis(self, area_filter=None):
        """
        Busca os KPIs reais do painel com base na análise do schema.
        Suporta filtro por Área (Departamento/Subtipo).
        """
        logger.info(f"📊 Buscando KPIs reais do Painel INA (Filtro: {area_filter or 'Todos'})...")

        filters_dax = ""
        if area_filter:
            filters_dax += f", 'Competencia'[Area.1.Subtipo ] = \"{area_filter}\""

        # Filtros Globais Obrigatórios
        # 1. Area <> InterCompany
        # 2. Status IN {ATRASADO, A VENCER, VENCE HOJE}
        global_filter = """
            'Competencia'[area] <> "InterCompany",
            'Competencia'[status_titulo] IN {"ATRASADO", "A VENCER", "VENCE HOJE"}
        """

        # Filtro de Faixa de Atraso para Top 10 (até 90 dias)
        # Ordem_Faixa_Atraso: 1=0-30d, 2=31-60d, 3=61-90d (numérico, exclui nulls)
        # NÃO filtra por status - dashboard inclui ATRASADO, A VENCER e VENCE HOJE
        filter_90_days = """
            'Competencia'[Ordem_Faixa_Atraso] IN {1, 2, 3}
        """

        # Query KPIs
        query_kpis = f"""
        EVALUATE 
        ROW(
            "Card_Vencendo_Hoje", CALCULATE([Card_Vencendo_Hoje], {global_filter} {filters_dax}),
            "Card_Inadimplencia_Ate_2_Dias", CALCULATE([Card_Inadimplencia_Ate_2_Dias], {global_filter} {filters_dax}),
            "Card_Inadimplencia_3_Mais_Dias", CALCULATE([Card_Inadimplencia_3_Mais_Dias], {global_filter} {filters_dax}),
            "Card_Media_Atraso", CALCULATE([Card_Media_Atraso], {global_filter} {filters_dax}),
            "Card_Inadimplencia_TOTAL", CALCULATE([Card_Inadimplencia_TOTAL], {global_filter} {filters_dax}),
            "Card_INTERCOMPANY", CALCULATE([Card_INTERCOMPANY], {global_filter} {filters_dax}), 
            "Card_QtdAtraso", CALCULATE([Card_QtdAtraso], {global_filter} {filters_dax})
        )
        """

        # Query Top 10 Clientes (Ranking Inadimplencia até 90 dias)
        # Agrupado por Nome Fantasia
        # Valor = Soma de valor_contas_receber
        # Dias = Media de DATEDIFF(data_vencimento, TODAY())
        query_top10 = f"""
        EVALUATE
        TOPN(
            10,
            ADDCOLUMNS(
                CALCULATETABLE(
                    VALUES('Competencia'[nome_fantasia]),
                    {global_filter} {filters_dax},
                    {filter_90_days}
                ),
                "Valor", CALCULATE(
                    SUM('Competencia'[valor_contas_receber]),
                    {global_filter} {filters_dax},
                    {filter_90_days}
                ),
                "Dias_Atraso", CALCULATE(
                    MAXX('Competencia', DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)),
                    {global_filter} {filters_dax},
                    {filter_90_days}
                )
            ),
            [Valor], DESC
        )
        """

        try:
            logger.info(f"🧐 Executing DAX Query for KPIs:\n{query_kpis}")
            # Busca KPIs
            kpis = self.powerbi.execute_dax(query_kpis)

            logger.info(f"📥 Result Raw KPIs: {kpis}")

            # Se a primeira query falhar, assumimos que todo o acesso falhou
            if not kpis:
                logger.error(f"❌ Query de KPIs retornou vazio/None para área {area_filter}.")
                if area_filter:
                    return None
                return self.fetch_connectivity_fallback()

            # Normalizar chaves (remover colchetes [Key] -> Key)
            # E Mapear para o formato do InaRenderer
            raw_kpis = kpis[0]
            normalized_kpis = {}

            # Mapa de De -> Para
            key_map = {
                "Card_Vencendo_Hoje": "VencendoHoje",
                "Card_Inadimplencia_TOTAL": "Total",
                "Card_Media_Atraso": "MediaAtraso",
                "Card_Inadimplencia_Ate_2_Dias": "Conciliacao",
            }

            for k, v in raw_kpis.items():
                clean_key = k.strip("[]")
                # Se estiver no mapa, usa o nome mapeado, senao mantem original
                final_key = key_map.get(clean_key, clean_key)
                normalized_kpis[final_key] = v

            logger.info(f"Keys Normalizadas: {list(normalized_kpis.keys())}")

            # Checar se os valores internos sao None
            if all(v is None for v in normalized_kpis.values()):
                logger.warning("⚠️ Atenção: Query retornou uma linha, mas todos os valores são None!")

            # Busca Top 10 (Opcional)
            top10 = []
            try:
                res_top10 = self.powerbi.execute_dax(query_top10)
                if res_top10:
                    # Normalizar chaves do Top 10 também
                    top10 = []
                    for item in res_top10:
                        norm_item = {}
                        for k, v in item.items():
                            # Normalizar chaves:
                            # 'Competencia[nome_fantasia]' -> 'nome_fantasia'
                            # '[Valor]' -> 'Valor'
                            # '[Dias_Atraso]' -> 'Dias_Atraso'
                            clean_k = k.replace("Competencia[", "").strip("[]")
                            norm_item[clean_k] = v

                        # Fallback nome
                        if "nome_fantasia" not in norm_item:
                            norm_item["nome_fantasia"] = norm_item.get("Cliente", "Desconhecido")

                        # Garantir dias positivos (DATEDIFF retorna negativo se vencimento futuro)
                        if "Dias_Atraso" in norm_item and isinstance(norm_item["Dias_Atraso"], (int, float)):
                            norm_item["Dias_Atraso"] = abs(int(norm_item["Dias_Atraso"]))

                        top10.append(norm_item)

                    # Ordenar por valor DESC (TOPN seleciona top 10 mas não garante ordem)
                    top10.sort(key=lambda x: float(x.get("Valor", 0) or 0), reverse=True)

                    logger.info(f"Dados Top 10 Raw ({len(top10)} items): {top10[:2]}...")
                else:
                    logger.warning("Query Top 10 retornou vazio.")
            except Exception as e:
                logger.warning(f"Falha ao buscar Top 10: {e}")
                top10 = []

            return {"kpis": normalized_kpis, "top10": top10}

        except Exception as e:
            logger.error(f"Erro ao executar queries DAX: {e}")
            return None  # Retorna None se falhar com filtro, para não mandar dados errados

    def fetch_connectivity_fallback(self):
        logger.info("Tentando fallback de conectividade...")
        try:
            res = self.powerbi.execute_dax('EVALUATE ROW("Status", "Conectado (Sem KPI)", "Hora", NOW())')
            return {"kpis": res[0], "top10": []} if res else None
        except Exception:
            return None

    def run(self, recipients=None, template_content=None):
        logger.info("=== AUTOMAÇÃO PAINEL INA ===")

        if not recipients:
            logger.warning("Sem destinatários para envio.")
            return

        # 1. Agrupar destinatários por Área
        grouped_recipients = {}

        for r in recipients:
            area = r.get("area")
            tags = r.get("tags", [])

            if not area and tags:
                for t in tags:
                    if t.startswith("area:"):
                        area = t.split(":")[1].strip()
                        break

            if not area or area.upper() in ["DIRETORIA", "GLOBAL", "GERAL"]:
                area_key = "GLOBAL"
            else:
                area_key = area.upper()

            if area_key not in grouped_recipients:
                grouped_recipients[area_key] = []
            grouped_recipients[area_key].append(r)

        logger.info(f"Destinatários agrupados: {list(grouped_recipients.keys())}")

        # 2. Processar cada grupo (Área)
        renderer = InaRenderer()

        for area_key, recip_list in grouped_recipients.items():
            logger.info(f"🔄 Processando área: {area_key}")

            area_filter = None if area_key == "GLOBAL" else area_key.title()

            # 2.1 Buscar Dados
            data = self.fetch_kpis(area_filter=area_filter)

            if not data:
                logger.error(f"Falha ao buscar dados para área {area_key}. Pulando envio.")
                continue

            kpis = data.get("kpis", {})
            top10 = data.get("top10", [])

            # 2.2 Gerar Imagem
            try:
                # Limpar e formatar KPIs
                kpis_clean = {}
                for k, v in kpis.items():
                    is_curr = k != "MediaAtraso"
                    kpis_clean[k] = self._clean_card_value(v, is_currency=is_curr)

                # Limpar e formatar Top 10
                top10_clean = []
                for item in top10:
                    new_item = item.copy()
                    # Limpar Valor
                    if "Valor" in new_item:
                        new_item["Valor"] = self._clean_card_value(new_item["Valor"], is_currency=True)
                    # Limpar Dias
                    if "Dias_Atraso" in new_item:
                        new_item["Dias_Atraso"] = self._clean_card_value(new_item["Dias_Atraso"], is_currency=False)
                    top10_clean.append(new_item)

                filename = "ina_report_global.png" if area_key == "GLOBAL" else f"ina_report_{area_key.lower()}.png"
                output_path = os.path.join(os.path.dirname(__file__), filename)

                display_area = "GERAL" if area_key == "GLOBAL" else area_key

                renderer.generate_image(
                    kpis_clean,
                    top10_clean,
                    output_path=output_path,
                    area_name=display_area,
                )
                logger.info(f"Relatório {area_key} gerado em: {output_path}")
            except Exception as e:
                logger.error(f"Erro ao gerar imagem para {area_key}: {e}")
                continue

            # 2.3 Enviar para destinatários do grupo
            for r in recip_list:
                nome = r.get("name") or r.get("nome", "Gestor")
                phone = r.get("phone") or r.get("telefone")

                if not phone:
                    continue

                caption = f"📊 *Painel INA [{display_area}] - {datetime.now().strftime('%d/%m/%Y')}*\nOlá {nome}, segue o resumo atualizado."

                try:
                    self.whatsapp.send_file(group_id=phone, file_path=output_path, caption=caption)
                    logger.info(f"Imagem ({area_key}) enviada para {nome} ({phone})")
                except Exception as e:
                    logger.error(f"Erro ao enviar para {nome}: {e}")

    def _clean_card_value(self, value, is_currency=True):
        """
        Limpa e formata valores.
        Suporta Raw (float/int) e Texto/HTML.
        """
        if value is None:
            return "-"

        # 1. Se for numérico nativo (float/int), formata direto
        if isinstance(value, (int, float)):
            if is_currency:
                # Formata PT-BR: R$ 1.234,56
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                # Formata inteiro
                return str(int(value))

        value_str = str(value)

        try:
            import re

            # 2. Remove HTML
            if "<" in value_str and ">" in value_str:
                value_str = re.sub(r"<style>.*?</style>", "", value_str, flags=re.DOTALL)
                value_str = re.sub(r"<[^<]+?>", "", value_str)

            # Normalizar espaços
            value_str = " ".join(value_str.split())

            # 3. Extração via Regex (para strings sujas que sobraram)
            if is_currency:
                # Procura padrao monetario
                match = re.search(r"(R\$\s?[\d\.,]+)", value_str)
                if match:
                    clean = match.group(1).replace(" ", "")
                    return clean.replace("R$", "R$ ")
            else:
                # Procura números
                digits = re.findall(r"(\d+)", value_str)
                if digits:
                    return digits[-1]

            return value_str.strip()

        except Exception as e:
            logger.warning(f"Erro ao limpar valor '{value}': {e}")
            return str(value)


if __name__ == "__main__":
    # Modo de Teste: Enviar para número específico
    automation = InaAutomation()

    # Remove temporary probe files
    for f in [
        "new_probe.txt",
        "new_probe_utf8.txt",
        "modules/ina/list_datasets.py",
        "modules/ina/probe_new_id.py",
    ]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    # 1. Executa o disparo de teste segmentado
    destinatarios_teste = [
        {
            "nome": "Victor (Diretoria)",
            "telefone": "5551998129077",
            "area": "DIRETORIA",
        },
        {
            "nome": "Victor (Tecnologia)",
            "telefone": "5551998129077",
            "area": "TECNOLOGIA",
        },
    ]

    logger.info("🚀 Iniciando disparo de TESTE manual (Segmentado - Novo Painel)...")
    automation.run(recipients=destinatarios_teste)
    logger.info("✅ Processo de teste finalizado.")
