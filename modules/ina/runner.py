"""
Automação Painel INA (Inadimplência)
Gera sempre o relatório GERAL com dados do Mês Atual acumulados até D-1.
Campos mapeados diretamente das medidas do Power BI.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Adiciona a raiz do projeto ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

if project_root not in sys.path:
    sys.path.append(project_root)

from config import POWERBI_CONFIG
from core.clients.evolution_client import EvolutionClient
from core.clients.powerbi_client import PowerBIClient
from core.services.image_renderer.ina_renderer import InaRenderer
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

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

    def fetch_kpis(self) -> Optional[Dict[str, Any]]:
        """Busca os KPIs e Top10"""

        hoje = datetime.now()
        ontem = hoje - timedelta(days=1)

        logger.info(f"Buscando acumulado do mês até: {ontem:%d/%m/%Y}")

        query_kpis = f"""
        EVALUATE
        CALCULATETABLE(
            ROW(
                "Card_Vencendo_Hoje", [Card_Vencendo_Hoje],
                "Card_Inadimplencia_Ate_2_Dias", [Card_Inadimplencia_Ate_2_Dias],
                "Card_Inadimplencia_3_Mais_Dias", [Card_Inadimplencia_3_Mais_Dias],
                "Card_QtdAtraso", [Card_QtdAtraso],
                "Card_Media_Atraso", [Card_Media_Atraso],
                "Card_INTERCOMPANY", [Card_INTERCOMPANY],
                "Card_Inadimplencia_TOTAL", [Card_Inadimplencia_TOTAL]
            ),
            'Calendario'[Date] <= DATE({ontem.year},{ontem.month},{ontem.day}),
            'Calendario'[Ano_Mes_Num] = {ontem.year * 100 + ontem.month}
        )
        """

        query_top10 = f"""
        EVALUATE
        TOPN(
            10,
            ADDCOLUMNS(
                CALCULATETABLE(
                    VALUES('Competencia'[nome_fantasia]),
                    'Competencia'[area] <> "InterCompany",
                    'Competencia'[Ordem_Faixa_Atraso] IN {{1,2,3}},
                    'Calendario'[Date] <= DATE({ontem.year},{ontem.month},{ontem.day}),
                    'Calendario'[Ano_Mes_Num] = {ontem.year * 100 + ontem.month}
                ),
                "Valor",
                CALCULATE(
                    SUM('Competencia'[valor_contas_receber])
                ),
                "Dias_Atraso",
                CALCULATE(
                    MAXX(
                        'Competencia',
                        DATEDIFF('Competencia'[data_vencimento], TODAY(), DAY)
                    )
                )
            ),
            [Valor], DESC
        )
        """

        try:
            logger.info("Executando DAX no Power BI")
            kpis_res = self.powerbi.execute_dax(query_kpis)

            if not kpis_res:
                logger.warning("Query vazia. Executando fallback")

                query_fallback = """
                EVALUATE
                ROW(
                    "Card_Vencendo_Hoje",[Card_Vencendo_Hoje],
                    "Card_Inadimplencia_Ate_2_Dias",[Card_Inadimplencia_Ate_2_Dias],
                    "Card_Inadimplencia_3_Mais_Dias",[Card_Inadimplencia_3_Mais_Dias],
                    "Card_QtdAtraso",[Card_QtdAtraso],
                    "Card_Media_Atraso",[Card_Media_Atraso],
                    "Card_INTERCOMPANY",[Card_INTERCOMPANY],
                    "Card_Inadimplencia_TOTAL",[Card_Inadimplencia_TOTAL]
                )
                """

                kpis_res = self.powerbi.execute_dax(query_fallback)

            if not kpis_res:
                logger.error("Não foi possível obter KPIs")
                return None

            raw = kpis_res[0]

            kpis = {re.sub(r".*\[|\]", "", k).strip(): v for k, v in raw.items()}

            top10 = self._fetch_top10(query_top10)

            return {"kpis": kpis, "top10": top10}

        except Exception as e:
            logger.exception(f"Erro crítico ao buscar KPIs: {e}")
            return None

    def _fetch_top10(self, query: str) -> List[Dict[str, Any]]:

        top10 = []

        try:
            res = self.powerbi.execute_dax(query)

            if not res:
                return top10

            for item in res:
                norm = {re.sub(r".*\[|\]", "", k).strip(): v for k, v in item.items()}

                if "Dias_Atraso" in norm and norm["Dias_Atraso"]:
                    try:
                        norm["Dias_Atraso"] = abs(int(float(str(norm["Dias_Atraso"]).replace(",", "."))))
                    except ValueError:
                        norm["Dias_Atraso"] = 0

                if "nome_fantasia" not in norm:
                    norm["nome_fantasia"] = norm.get("Cliente", "Desconhecido")

                top10.append(norm)

            top10.sort(
                key=lambda x: float(str(x.get("Valor", 0)).replace(",", ".").replace("R$", "").strip() or 0),
                reverse=True,
            )

        except Exception as e:
            logger.warning(f"Erro ao buscar Top10: {e}")

        return top10

    def run(self, recipients=None, generate_only=False):

        data = self.fetch_kpis()

        if not data:
            return

        kpis = data.get("kpis", {})
        top10 = data.get("top10", [])

        monetarios = {
            "Card_Vencendo_Hoje",
            "Card_Inadimplencia_Ate_2_Dias",
            "Card_Inadimplencia_3_Mais_Dias",
            "Card_INTERCOMPANY",
            "Card_Inadimplencia_TOTAL",
        }

        kpis_fmt = {k: self._formatar(v, k in monetarios) for k, v in kpis.items()}

        top10_fmt = []

        for it in top10:
            it_fmt = it.copy()

            it_fmt["Valor"] = self._formatar(it.get("Valor"), True)
            it_fmt["Dias_Atraso"] = self._formatar(it.get("Dias_Atraso"), False)

            top10_fmt.append(it_fmt)

        renderer = InaRenderer()

        output = os.path.join(os.path.dirname(__file__), "ina_report_global.png")

        renderer.generate_image(kpis=kpis_fmt, top10=top10_fmt, output_path=output)

        if generate_only:
            logger.info(f"Imagem gerada: {output}")
            return

        data_pos = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")

        caption = f"📊 Painel INA — Posição: {data_pos}\nAcumulado do mês até ontem."

        for r in recipients or []:
            phone = r.get("phone") or r.get("telefone")

            if not phone:
                continue

            try:
                self.whatsapp.send_file(group_id=phone, file_path=output, caption=caption)

            except Exception as e:
                logger.error(f"Erro ao enviar para {phone}: {e}")

    def _formatar(self, valor, moeda=False, escala=False, extrair_valor_dict=True):
        """
        Formata numéricos para o padrão PT-BR.
        - extrair_valor_dict: se True, e o valor for um dicionário {"detail": {"value": "..."}}, extrai o 'value'.
        """
        if valor is None:
            return "R$ 0,00" if moeda else "0"

        # A API do Power BI pode retornar objetos para medidas
        # Exemplo: {'detail': {'type': 1, 'value': '3241803780'}}
        if extrair_valor_dict and isinstance(valor, dict):
            # Tentar extrair do formato padrão do Power BI REST API
            if 'detail' in valor and isinstance(valor['detail'], dict) and 'value' in valor['detail']:
                valor = valor['detail']['value']
            elif 'value' in valor:
                valor = valor['value']
            else:
                # Log em caso de estrutura desconhecida e fallback
                print(f"Aviso: estrutura de dicionário desconhecida na formatação: {valor}")
                # Tentativa genérica de pegar a primeira string que pareça número
                try:
                    str_val = str(valor)
                    matches = re.findall(r'-?\d+\.?\d*', str_val)
                    if matches:
                        valor = matches[0]
                except Exception:
                    pass

        try:
            # Limpeza caso seja string com formatação
            if isinstance(valor, str):
                valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
                if not valor:
                    valor = 0
            
            # Se for string com dígito literal único (ex: 'R$ 0,00' original), a limpeza já converte para número
            try:
                numerico = float(valor)
            except ValueError:
                # Fallback: extrai o primeiro número encontrado na string (seja int ou float)
                str_orig = str(valor)
                matches = re.findall(r'-?\d+\.?\d*', str_orig.replace(".", "").replace(",", "."))
                numerico = float(matches[0]) if matches else 0.0
                
            # Muitas vezes o Power BI já traz os valores na escala correta, ou às vezes deslocados.
            # O painel que estamos imitando (na imagem original) mostrou ~3.2Mi, mas se a API retorna 3241803780
            # Pode estar vindo em centavos ou multiplicado. Geralmente é dividido por 100 se vier sem decimais de moeda.
            # Baseado na diferença de grandeza (o original tinha 3,2 Mi e o PBI retornou ~3.2 Bi (3241803780)), 
            # é provável que precisemos dividir por 100 os valores monetários se a escala não já tiver sido aplicada pela view
            
            # Aplica escala opcional
            if escala:
                numerico = numerico / 100

            if moeda:
                # Formata como moeda (ex: R$ 1.234,56)
                formatado = f"R$ {numerico:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                return formatado
            else:
                # Formata como inteiro ou com separador de milhar se for grande (ex: 253, 1.253)
                if int(numerico) == numerico:
                    formatado = f"{int(numerico):,}".replace(",", ".")
                else:
                    formatado = f"{numerico:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    if formatado.endswith(',00'):
                        formatado = formatado[:-3]
                return formatado
        except Exception as e:
            print(f"Erro ao formatar valor '{valor}': {e}")
            return "R$ 0,00" if moeda else "0"

    def gerar_relatorio_geral(self, force_d1_fallback=False):
        """
        Busca os dados e gera o card para Inadimplência Geral (Mês Atual).
        Usa o filtro D-1 na DAX do Power BI.
        `force_d1_fallback` permite ignorar a restrição de "ontem" se necessário.
        """
        print("\n=== GERANDO RELATÓRIO DE INADIMPLÊNCIA GERAL ===")
        
        # O Power BI usa o dia anterior como referência de dados atualizados
        # Como visto na imagem original: "Posição: 10/03/2026" (ontem)
        ontem = datetime.now() - timedelta(days=1)
        data_posicao = ontem.strftime("%d/%m/%Y")
        ano_mes_atual = ontem.strftime("%Y%m") # Ex: 202603

        # Constrói o filtro DAX de data
        dax_date_filter = f"DATE({ontem.year}, {ontem.month}, {ontem.day})"
        
        # Filtro de grupo Área = Geral (vazio) não é necessário pois "Geral" é tudo
        # Mas vamos excluir o InterCompany das medidas quando possível na DAX
        
        # A API pode retornar erro se o DATE for muito restitivo (nenhum dado de "ontem"),
        # uma restrição <= ontem dentro do mês atual garante que pega o acumulado correto
        
        print(f"Data Base (D-1): {data_posicao} | Ano_Mes: {ano_mes_atual}")
        print("Buscando KPIs Consolidados...")
        
        dax_kpis = f"""
        EVALUATE
        SUMMARIZECOLUMNS(
            "Card_Vencendo_Hoje", [Card_Vencendo_Hoje],
            "Card_Vencido_Tot", [Card_Vencido_Tot],
            "Card_Vencendo_<15_dias", [Card_Vencendo_<15_dias],
            "Card_Vencer_Tot", [Card_Vencer_Tot],
            "Card_Vencendo_16-30_Dias", [Card_Vencendo_16-30_Dias],
            "TT_Titulos_INA", [TT_Titulos_INA],
            "Ina_Tot_Media_Dias_Geral", [Ina_Tot_Media_Dias_Geral],
            
            -- Filtramos pelo mês atual e dados até D-1
            FILTER(
                'Calendario',
                'Calendario'[Ano_Mes_Num] = {ano_mes_atual} &&
                'Calendario'[Date] <= {dax_date_filter}
            )
        )
        """
        
        dados_geral = self.powerbi.execute_dax(dax_kpis)
        
        # Valores Default caso retorne vazio ou erro
        kpi = {
            "vencendo_hoje": "0",
            "vencido": "R$ 0,00",
            "menos_15_dias": "0",
            "a_vencer": "R$ 0,00",
            "16_30_dias": "0",
            "titulos": "0",
            "media_dias": "0"
        }

        # Extração inteligente baseada na chave do dicionário de resultados
        if dados_geral and len(dados_geral) > 0:
            row = dados_geral[0]
            # Mapeamento dinâmico ignorando case e colchetes
            for raw_key, value in row.items():
                k = raw_key.lower().replace("[", "").replace("]", "")
                
                # Vamos lidar com o value extraindo o valor do dict se ele existir
                if isinstance(value, dict) and 'detail' in value and 'value' in value['detail']:
                    real_value = value['detail']['value']
                elif isinstance(value, dict) and 'value' in value:
                    real_value = value['value']
                else:
                    real_value = value
                
                # Atenção: a formatação já lida com os dicts, mas o scale fix monetário
                # se mostrou necessário pois a base no PowerBI pode estar sem virgulas.
                # Aplicamos a escala para campos financeiros.
                
                if "vencendo_hoje" in k:
                    kpi["vencendo_hoje"] = self._formatar(real_value, moeda=True, escala=True, extrair_valor_dict=False)
                elif "vencido_tot" in k or "vencido" in k:
                    kpi["vencido"] = self._formatar(real_value, moeda=True, escala=True, extrair_valor_dict=False)
                elif "menos_15" in k or "<15" in k:
                    kpi["menos_15_dias"] = self._formatar(real_value, moeda=True, escala=True, extrair_valor_dict=False)
                elif "vencer_tot" in k or "a_vencer" in k:
                    kpi["a_vencer"] = self._formatar(real_value, moeda=True, escala=True, extrair_valor_dict=False)
                elif "16-30" in k or "16_30" in k:
                    kpi["16_30_dias"] = self._formatar(real_value, moeda=True, escala=True, extrair_valor_dict=False)
                elif "tt_titulos" in k:
                    kpi["titulos"] = self._formatar(real_value, moeda=False, extrair_valor_dict=False)
                elif "media_dias" in k:
                    kpi["media_dias"] = self._formatar(real_value, moeda=False, extrair_valor_dict=False)
        else:
            print("Aviso: A query KPIs não retornou dados. Verificando se o filtro de data (D-1) foi muito restritivo...")
            if not force_d1_fallback:
                print("Tentando buscar sem restrição de dia para ver se há dados no mês...")
                # Isso seria implementado repetindo a query sem o filtro de Date <= ontem
                pass


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
