"""
Automação Painel INA (Inadimplência)
Gera o relatório GERAL com dados acumulados do Mês Atual até D-1.
As medidas do Power BI já têm contexto próprio — NÃO aplicar filtros de data
sobre elas no DAX (isso zera os resultados). Apenas buscar com EVALUATE ROW.
"""

import argparse
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template

from src.config import POWERBI_CONFIG
from src.core.clients.evolution_client import EvolutionClient
from src.core.clients.powerbi_client import PowerBIClient
from src.core.services.notification_service import NotificationService
from src.core.services.supabase_service import SupabaseService
from src.core.utils.greeting import get_saudacao
from src.core.utils.logger import get_logger
from src.modules.ina.renderer import InaRenderer

logger = get_logger("run_ina")

INA_DATASET_ID = POWERBI_CONFIG.get("ina_dataset_id")
INA_WORKSPACE_ID = POWERBI_CONFIG.get("ina_workspace_id")


class InaAutomation:
    def __init__(self):
        if not INA_DATASET_ID or not INA_WORKSPACE_ID:
            raise ValueError("Dataset ou Workspace ID não configurados.")

        self.powerbi = PowerBIClient(workspace_id=INA_WORKSPACE_ID, dataset_id=INA_DATASET_ID)
        self.whatsapp = EvolutionClient()
        self.supabase = SupabaseService()

    def _extrair_valor(self, v: Any) -> Any:
        """
        Normaliza o retorno da API do Power BI.
        As medidas customizadas do Power BI retornam HTML no formato:
          <style>...</style>
          <div class='cardContainer'>
            <div class='cardTitle'>TITULO</div>
            <div class='cardValor'>R$ 30.005.730</div>
          </div>
        Extrai o conteudo da div.cardValor para obter o valor real.
        """
        # Normaliza dicionarios de medida
        if isinstance(v, dict):
            if "detail" in v and isinstance(v["detail"], dict):
                v = v["detail"].get("value", v["detail"])
            elif "value" in v:
                v = v["value"]

        if not isinstance(v, str):
            return v

        # Verifica se tem HTML antes de processar
        if "<" not in v:
            return v.strip()

        # Tenta extrair o valor da div.cardValor (padrao das medidas INA no Power BI)
        match_card_valor = re.search(
            r"<div[^>]*class=['\"]cardValor['\"][^>]*>\s*([^<]+?)\s*</div>",
            v,
            re.DOTALL | re.IGNORECASE,
        )
        if match_card_valor:
            return match_card_valor.group(1).strip()

        # Fallback: remove todas as tags HTML e retorna o texto limpo
        import html as _html_mod

        sem_tags = re.sub(r"<[^>]+>", "", v)
        # Remove blocos CSS (entre { e })
        sem_css = re.sub(r"\{[^}]*\}", "", sem_tags)
        texto_limpo = _html_mod.unescape(sem_css).strip()
        return texto_limpo if texto_limpo else v

    def _formatar(self, valor: Any, moeda: bool = False) -> str:
        """
        Converte o valor retornado pela API do Power BI para string formatada em PT-BR.
        - moeda=True  -> 'R$ 1.234,56'
        - moeda=False -> '253'
        """
        valor = self._extrair_valor(valor)  # normaliza dicts e limpa HTML

        if valor is None:
            return "R$ 0,00" if moeda else "0"

        try:
            if isinstance(valor, (int, float)):
                numerico = float(valor)
            elif isinstance(valor, str):
                texto = valor.strip()
                if not texto:
                    return "R$ 0,00" if moeda else "0"

                # Tenta extrair padrao monetario PT-BR: R$ 1.234,56 ou R$ 30.005.730
                # ou numerico com separadores: 30.005.730 / 253
                # Padrao priorizado: encontra sequencia de digitos com . e , opcionais
                match = re.search(r"[\d]+(?:[.]\d{3})*(?:,\d{1,2})?", texto)
                if match:
                    num_str = match.group(0)
                    # Converte PT-BR para float: 30.005.730 -> 30005730 | 151.794,50 -> 151794.50
                    if "," in num_str:
                        # Tem decimal: 151.794,50 -> 151794.50
                        partes = num_str.rsplit(",", 1)
                        inteira = partes[0].replace(".", "")
                        decimal = partes[1]
                        numerico = float(f"{inteira}.{decimal}")
                    else:
                        # Sem decimal: 30.005.730 -> 30005730
                        numerico = float(num_str.replace(".", ""))
                else:
                    # Fallback: remove tudo que nao e digito ou ponto/virgula
                    limpo = re.sub(r"[^\d.,]", "", texto)
                    limpo = limpo.replace(".", "").replace(",", ".")
                    numerico = float(limpo) if limpo else 0.0
            else:
                numerico = float(valor)

            if moeda:
                return f"R$ {numerico:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                return f"{int(numerico):,}".replace(",", ".")

        except Exception as e:
            logger.warning(f"Erro ao formatar valor '{str(valor)[:80]}': {e}")
            return "R$ 0,00" if moeda else "0"

    def fetch_kpis(self) -> Optional[Dict[str, Any]]:
        """
        Busca os KPIs e Top10 do Power BI com filtro de calendário do mês_vigente.
        """
        # Referência Hoje (D-0)
        hoje = datetime.now()
        ano_mes = int(hoje.strftime("%Y%m"))
        logger.info(
            f"Buscando KPIs INA (referência D-0: {hoje.strftime('%d/%m/%Y')}, Calendario[AnoMes_Ordenacao]={ano_mes})"
        )

        query_kpis = f"""
        EVALUATE
        ROW(
            "Card_Vencendo_Hoje",
                CALCULATE([Card_Vencendo_Hoje], 'Calendario'[AnoMes_Ordenacao] = {ano_mes}),
            "Card_Inadimplencia_Ate_2_Dias",
                CALCULATE([Card_Inadimplencia_Ate_2_Dias], 'Calendario'[AnoMes_Ordenacao] = {ano_mes}),
            "Card_Inadimplencia_3_Mais_Dias",
                CALCULATE([Card_Inadimplencia_3_Mais_Dias], 'Calendario'[AnoMes_Ordenacao] = {ano_mes}),
            "Card_QtdAtraso",
                CALCULATE([Card_QtdAtraso], 'Calendario'[AnoMes_Ordenacao] = {ano_mes}),
            "Card_Media_Atraso",
                CALCULATE([Card_Media_Atraso], 'Calendario'[AnoMes_Ordenacao] = {ano_mes}),
            "Card_INTERCOMPANY",
                FORMAT(
                    VAR val = CALCULATE(
                        COALESCE([total2], 0),
                        'Intercompany'[Personalizar] = "Com Intercompany",
                        'Calendario'[AnoMes_Ordenacao] = {ano_mes}
                    )
                    RETURN IF(val < 0, 0, val),
                    "R$ #,##0"
                ),
            "Card_Inadimplencia_TOTAL",
                FORMAT(
                    CALCULATE(
                        COALESCE([total2], 0),
                        'Intercompany'[Personalizar] = "Sem Intercompany"
                    ),
                    "R$ #,##0"
                )
        )
        """

        query_top10 = """
        EVALUATE
        TOPN(
            10,
            FILTER(
                ADDCOLUMNS(
                    VALUES('Competencia'[razao_social]),
                    "Dias", CALCULATE(
                        MAXX(
                            'Competencia',
                            DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)
                        ),
                        'Competencia'[data_vencimento] < TODAY(),
                        ISBLANK('Competencia'[data_lancamento])
                    ),
                    "Valor", CALCULATE(
                        SUM('Competencia'[valor_contas_receber]),
                        'Competencia'[data_vencimento] < TODAY(),
                        ISBLANK('Competencia'[data_lancamento])
                    )
                ),
                [Dias] >= 3 && [Dias] <= 90 && [Valor] > 0
            ),
            [Valor], DESC
        )
        """

        try:
            logger.info("Executando query KPIs no Power BI")
            kpis_res = self.powerbi.execute_dax(query_kpis)

            if not kpis_res:
                logger.error("Query KPIs retornou vazio. Abortando.")
                return None

            raw = kpis_res[0]
            # Normaliza chaves: remove prefixo e colchetes (ex: "[Card_Vencendo_Hoje]" → "Card_Vencendo_Hoje")
            kpis = {re.sub(r".*\[|\]", "", k).strip(): v for k, v in raw.items()}

            logger.info(f"KPIs recebidos: {list(kpis.keys())}")
            for campo, val in kpis.items():
                logger.debug(f"  {campo} = {val!r}")

            top10 = self._fetch_top10(query_top10)

            return {"kpis": kpis, "top10": top10}

        except Exception as e:
            logger.exception(f"Erro crítico ao buscar KPIs: {e}")
            return None

    def _fetch_top10(self, query: str) -> List[Dict[str, Any]]:
        """Busca e normaliza o Top10 de inadimplentes."""
        top10 = []

        try:
            res = self.powerbi.execute_dax(query)

            if not res:
                logger.warning("Top10 retornou vazio.")
                return top10

            for item in res:
                # Normaliza chaves
                norm = {re.sub(r".*\[|\]", "", k).strip(): self._extrair_valor(v) for k, v in item.items()}

                # Garante o campo nome_fantasia (vindo de razao_social)
                norm["nome_fantasia"] = norm.get("razao_social", norm.get("Cliente", "Desconhecido"))

                # Normaliza Dias_Atraso para inteiro (vindo do campo "Dias")
                dias_val = norm.get("Dias", norm.get("Dias_Atraso"))
                if dias_val is not None:
                    try:
                        norm["Dias_Atraso"] = abs(int(float(str(dias_val).replace(",", "."))))
                    except ValueError:
                        norm["Dias_Atraso"] = 0

                # Normaliza Valor para float
                valor_val = norm.get("Valor")
                if valor_val is not None:
                    try:
                        norm["Valor"] = float(str(valor_val).replace(",", "."))
                    except ValueError:
                        norm["Valor"] = 0.0

                top10.append(norm)

            # Ordena por valor descendente e aplica Rank manual (1 a 10)
            top10.sort(key=lambda x: x.get("Valor") or 0, reverse=True)
            for i, item in enumerate(top10):
                item["Rank"] = i + 1

        except Exception as e:
            logger.warning(f"Erro ao buscar Top10: {e}")

        return top10

    def run(self, recipients=None, generate_only=False, template_content=None):
        """Executa a automação: busca dados, gera imagem e envia por WhatsApp."""
        data = self.fetch_kpis()

        if not data:
            logger.error("Não foi possível obter dados. Relatório não gerado.")
            return

        kpis = data.get("kpis", {})
        top10 = data.get("top10", [])

        # Campos monetários vs numéricos
        monetarios = {
            "Card_Vencendo_Hoje",
            "Card_Inadimplencia_Ate_2_Dias",
            "Card_Inadimplencia_3_Mais_Dias",
            "Card_INTERCOMPANY",
            "Card_Inadimplencia_TOTAL",
        }

        kpis_fmt = {k: self._formatar(v, k in monetarios) for k, v in kpis.items()}

        logger.info("KPIs formatados:")
        for k, v in kpis_fmt.items():
            logger.info(f"  {k}: {v}")

        # Formata Top10 para o renderer
        top10_fmt = []
        for it in top10:
            it_fmt = it.copy()
            it_fmt["Valor"] = self._formatar(it.get("Valor"), moeda=True)
            it_fmt["Dias_Atraso"] = self._formatar(it.get("Dias_Atraso"), moeda=False)
            top10_fmt.append(it_fmt)

        renderer = InaRenderer()
        output = os.path.join(os.path.dirname(__file__), "ina_report_global.png")
        renderer.generate_image(kpis=kpis_fmt, top10=top10_fmt, output_path=output)

        if generate_only:
            logger.info(f"Imagem gerada: {output}")
            return

        data_pos = datetime.now().strftime("%d/%m/%Y")

        # Resolve template: passado pelo schedule > banco > None (fallback hardcoded)
        if template_content:
            caption_template = template_content
        else:
            tmpl = self.supabase.get_template_by_name("Mensagem de Inadimplência")
            caption_template = tmpl["content"] if tmpl else None

        notification_service = NotificationService(self.supabase)
        batch: list[tuple] = []

        for r in recipients or []:
            phone = r.get("phone") or r.get("telefone")
            if not phone:
                continue

            nome = r.get("name") or r.get("nome") or "Colaborador"
            primeiro_nome = nome.split()[0].title()
            saudacao = get_saudacao()
            saudacao_lower = saudacao.lower()

            context = {
                "nome": primeiro_nome,
                "nome_completo": nome,
                "saudacao": saudacao,
                "saudacao_lower": saudacao_lower,
                "data": data_pos,
            }

            if caption_template:
                try:
                    if "{{" in caption_template:
                        caption = Template(caption_template).render(**context)
                    else:
                        caption = caption_template.format(**context)
                except Exception as e:
                    logger.error(f"Erro ao formatar template para {nome}: {e}")
                    caption = f"{saudacao}, {primeiro_nome}!\n\n📊 Painel INA — Posição: Hoje ({data_pos})"
            else:
                caption = f"{saudacao}, {primeiro_nome}!\n\n📊 Painel INA — Posição: Hoje ({data_pos})"

            batch.append((r, output, caption))

        results = notification_service.send_batch(batch, context_tag="ina")
        logger.info(f"[INA] Envios: {results['success']} ok, {results['failed']} falhas.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--payload", type=str)
    args = parser.parse_args()

    recipients = [{"telefone": "5551998129077"}]

    if args.payload:
        try:
            payload = json.loads(args.payload)
            recipients = payload.get("recipients", recipients)
        except json.JSONDecodeError:
            logger.error("Payload JSON inválido")

    InaAutomation().run(recipients=recipients, generate_only=args.generate_only)


if __name__ == "__main__":
    main()
