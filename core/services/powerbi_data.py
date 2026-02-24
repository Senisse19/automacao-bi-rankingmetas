"""
Serviço de Dados Power BI.
Responsável por buscar dados reais de metas e receitas do Power BI via DAX,
integrando diretamente com o modelo semântico mapeado.
"""

import json
from datetime import datetime, timedelta
from core.clients.powerbi_client import PowerBIClient
from utils.logger import get_logger

logger = get_logger("powerbi_data")


def format_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None or value == 0:
        return "-"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value):
    """Formata valor como percentual"""
    if value is None or value == 0:
        return ""
    return f"{value:.2f}%".replace(".", ",")


from core.services.dax_queries import (
    get_realizado_query,
    get_metas_com_op_query,
    get_percentuais_gs_query,
    get_percentuais_com_op_query,
    get_receitas_query,
    get_metas_dept_query,
    get_percentuais_dept_query,
    get_repasses_query,
    get_receitas_liquido_query,
)


from config import POWERBI_CONFIG


class PowerBIDataFetcher:
    """
    Classe responsável por buscar dados de metas do Power BI via consultas DAX.
    Gerencia autenticação e orquestra as chamadas para diferentes tabelas e medidas.
    """

    def __init__(self):
        self.client = PowerBIClient(
            workspace_id=POWERBI_CONFIG.get("metas_workspace_id"), dataset_id=POWERBI_CONFIG.get("metas_dataset_id")
        )
        self._authenticated = False

    def authenticate(self):
        """Realiza a autenticação no Power BI se ainda não estiver autenticado."""
        if not self._authenticated:
            self._authenticated = self.client.authenticate()
        return self._authenticated

    def _get_month_filter(self):
        """Retorna filtro de data para o mês atual"""
        now = datetime.now()
        return f"DATE({now.year}, {now.month}, 1)"

    def fetch_valores_realizados(self):
        """Busca os valores REALIZADOS de cada departamento (da tabela Medidas)."""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_realizado_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "Comercial": row.get("[Comercial]") or 0,
                    "Operacional": row.get("[Operacional]") or 0,
                    "Corporate": row.get("[Corporate]") or 0,
                    "Educação": row.get("[Educacao]") or 0,
                    "Expansão": row.get("[Expansao]") or 0,
                    "Franchising": row.get("[Franchising]") or 0,
                    "PJ": row.get("[PJ]") or 0,
                    "Tax": row.get("[Tax]") or 0,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar valores realizados: {e}")

        return {}

    def fetch_metas_comercial_operacional(self):
        """Busca as METAS específicas de Comercial e Operacional (da tabela Medidas) com filtro de data."""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_metas_com_op_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "Comercial": {
                        "meta1": row.get("[Comercial_Meta1]", 0),
                        "meta2": row.get("[Comercial_Meta2]", 0),
                        "meta3": row.get("[Comercial_Meta3]", 0),
                    },
                    "Operacional": {
                        "meta1": row.get("[Operacional_Meta1]", 0),
                        "meta2": row.get("[Operacional_Meta2]", 0),
                        "meta3": row.get("[Operacional_Meta3]", 0),
                    },
                }
        except Exception as e:
            logger.error(f"Erro ao buscar metas Comercial/Operacional: {e}")

        return {}

    def fetch_percentuais_gs(self):
        """Busca percentuais das metas GS (% Meta 1 GS, % Meta 2 GS, % Meta 3 GS)"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_percentuais_gs_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "pct_meta1": (row.get("[Pct_Meta1]") or 0) * 100,  # Converter para percentual
                    "pct_meta2": (row.get("[Pct_Meta2]") or 0) * 100,
                    "pct_meta3": (row.get("[Pct_Meta3]") or 0) * 100,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar percentuais GS: {e}")

        return {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0}

    def fetch_percentuais_comercial_operacional(self):
        """Busca percentuais de Comercial e Operacional"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_percentuais_com_op_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "Comercial": {
                        "pct_meta1": (row.get("[Com_Pct1]") or 0) * 100,
                        "pct_meta2": (row.get("[Com_Pct2]") or 0) * 100,
                        "pct_meta3": (row.get("[Com_Pct3]") or 0) * 100,
                    },
                    "Operacional": {
                        "pct_meta1": (row.get("[Op_Pct1]") or 0) * 100,
                        "pct_meta2": (row.get("[Op_Pct2]") or 0) * 100,
                        "pct_meta3": (row.get("[Op_Pct3]") or 0) * 100,
                    },
                }
        except Exception as e:
            logger.error(f"Erro ao buscar percentuais Comercial/Operacional: {e}")

        return {
            "Comercial": {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0},
            "Operacional": {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0},
        }

    def fetch_receitas(self):
        """Busca valores de receitas (Outras Receitas, Intercompany, Não Identificadas) da tabela Medidas"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_receitas_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "outras": row.get("[OutrasReceitas]") or 0,
                    "intercompany": row.get("[InterCompany]") or 0,
                    "nao_identificadas": row.get("[NaoIdentificada]") or 0,
                    "sem_categoria": row.get("[SemCategoria]") or 0,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar receitas: {e}")

        return {
            "outras": 0,
            "intercompany": 0,
            "nao_identificadas": 0,
            "sem_categoria": 0,
        }

    def fetch_repasses(self):
        """Busca valores de repasses do Power BI"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_repasses_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                # Mapeamento robusto: medidas que existem vs departamentos na UI
                repasses_dict = {
                    "Corporate": row.get("[Corporate_Repasse]") or 0,
                    "Tax": row.get("[Tax_Repasse]") or 0,
                    "Total_Geral": row.get("[Total_Repasse_Geral]") or 0,
                    # Departamentos sem medida específica de repasse no PBI (confirmado como R$ 0 pelo usuário)
                    "Educação": 0,
                    "Expansão": 0,
                    "Franchising": 0,
                    "PJ": 0,
                }
                # O total exibido no card de receitas deve ser o oficial do PBI
                repasses_dict["Total"] = repasses_dict["Total_Geral"]
                return repasses_dict
        except Exception as e:
            logger.error(f"Erro ao buscar repasses: {e}")

        return {"Corporate": 0, "Educação": 0, "Expansão": 0, "Franchising": 0, "PJ": 0, "Tax": 0, "Total": 0}

    def fetch_receitas_liquido(self):
        """Busca valores líquidos da Composição de Receitas"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_receitas_liquido_query(date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "Corporate": row.get("[Corporate_Liquido]") or 0,
                    "Educação": row.get("[Educacao_Liquido]") or 0,
                    "Expansão": row.get("[Expansao_Liquido]") or 0,
                    "Franchising": row.get("[Franchising_Liquido]") or 0,
                    "Tax": row.get("[Tax_Liquido]") or 0,
                    "PJ": row.get("[Tecnologia_Liquido]") or 0,
                    "Total_Comercial": row.get("[Total_Comercial]") or 0,
                    "Total_Operacional": row.get("[Total_Operacao]") or 0,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar receitas liquido: {e}")

        return {
            "Corporate": 0,
            "Educação": 0,
            "Expansão": 0,
            "Franchising": 0,
            "Tax": 0,
            "PJ": 0,
            "Total_Comercial": 0,
            "Total_Operacional": 0,
        }

    def fetch_metas_departamento(self, tabela, prefixo):
        """Busca metas de um departamento específico"""
        month_filter = self._get_month_filter()
        query = get_metas_dept_query(tabela, month_filter)

        try:
            result = self.client.execute_dax(query)
            if result:
                metas = {"meta1": 0, "meta2": 0, "meta3": 0}
                for row in result:
                    tipo = row.get(f"{tabela}[TIPO]", "")
                    valor = row.get(f"{tabela}[Metas]", 0)

                    if tipo == "Meta 1":
                        metas["meta1"] = valor
                    elif tipo == "Meta 2":
                        metas["meta2"] = valor
                    elif tipo == "Meta 3":
                        metas["meta3"] = valor

                return metas
        except Exception as e:
            logger.error(f"Erro ao buscar metas {tabela}: {e}")

        return {"meta1": 0, "meta2": 0, "meta3": 0}

    def fetch_percentuais_departamento(self, prefixo):
        """Busca percentuais de um departamento específico (% Meta 1/2/3 PREFIXO)"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"

        query = get_percentuais_dept_query(prefixo, date_filter_start, date_filter_end)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "pct_meta1": (row.get("[Pct1]") or 0) * 100,
                    "pct_meta2": (row.get("[Pct2]") or 0) * 100,
                    "pct_meta3": (row.get("[Pct3]") or 0) * 100,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar percentuais {prefixo}: {e}")

        return {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0}

    def fetch_all_data(self):
        """
        Orquestra a busca de TODOS os dados necessários para a automação.
        Retorna:
            - total_gs: Relatório consolidado da GS.
            - departamentos: Lista de relatórios por departamento.
            - receitas: Dados de outras receitas/intercompany.
        """
        if not self.authenticate():
            logger.error("Falha na autenticação com Power BI")
            return None, None, None

        logger.info("Buscando dados do Power BI...")

        # 1. Buscar valores realizados
        realizados = self.fetch_valores_realizados()

        # 2. Buscar receitas (Outras Receitas, Intercompany)
        receitas_raw = self.fetch_receitas()

        # 3. Buscar repasses por departamento (usa Dept_Descricao='Repasse')
        repasses = self.fetch_repasses()

        # 4. Buscar líquidos por departamento (realizado - repasse)
        liquido = self.fetch_receitas_liquido()

        # 4. Buscar metas GS (total)
        metas_gs = self.fetch_metas_departamento("GS_Metas", "GS")

        # 5. Buscar metas Comercial/Operacional
        metas_com_op = self.fetch_metas_comercial_operacional()

        # 6. Configuração dos outros departamentos
        departamentos_config = [
            ("Corporate", "Corporate_Metas", "CORPORATE"),
            ("Educação", "Educação_Metas", "EDUCACAO"),
            ("Expansão", "Expansão_Metas", "EXPANSAO"),
            ("Franchising", "Franchising_Metas", "FRANCHISING"),
            ("Tax", "TAX_Metas", "TAX"),
            ("Tecnologia", "PJ360_Metas", "PJ"),
        ]

        liq_comercial = liquido.get("Total_Comercial", 0)
        liq_operacional = liquido.get("Total_Operacional", 0)
        realizado_liquido_gs = liq_comercial + liq_operacional

        meta1_gs = metas_gs.get("meta1", 0)
        meta2_gs = metas_gs.get("meta2", 0)
        meta3_gs = metas_gs.get("meta3", 0)

        # Monta dados formatados para GS — agora usando valores Líquidos para o GS
        total_gs = {
            "meta1": format_currency(meta1_gs),
            "meta2": format_currency(meta2_gs),
            "meta3": format_currency(meta3_gs),
            "pct_meta1": (realizado_liquido_gs / meta1_gs * 100) if meta1_gs > 0 else 0,
            "pct_meta2": (realizado_liquido_gs / meta2_gs * 100) if meta2_gs > 0 else 0,
            "pct_meta3": (realizado_liquido_gs / meta3_gs * 100) if meta3_gs > 0 else 0,
            "realizado": format_currency(realizado_liquido_gs),
            "percent": format_percent((realizado_liquido_gs / meta1_gs * 100) if meta1_gs > 0 else 0),
        }

        departamentos = []

        # Comercial (agora líquido como padrão)
        com_metas = metas_com_op.get("Comercial", {})
        com_meta1 = com_metas.get("meta1", 0)
        com_meta2 = com_metas.get("meta2", 0)
        com_meta3 = com_metas.get("meta3", 0)

        departamentos.append(
            {
                "nome": "Comercial",
                "meta1": format_currency(com_meta1),
                "meta2": format_currency(com_meta2),
                "meta3": format_currency(com_meta3),
                "pct_meta1": (liq_comercial / com_meta1 * 100) if com_meta1 > 0 else 0,
                "pct_meta2": (liq_comercial / com_meta2 * 100) if com_meta2 > 0 else 0,
                "pct_meta3": (liq_comercial / com_meta3 * 100) if com_meta3 > 0 else 0,
                "realizado": format_currency(liq_comercial),
                "percent": format_percent((liq_comercial / com_meta1 * 100) if com_meta1 > 0 else 0),
            }
        )

        # Operacional (agora líquido como padrão)
        op_metas = metas_com_op.get("Operacional", {})
        op_meta1 = op_metas.get("meta1", 0)
        op_meta2 = op_metas.get("meta2", 0)
        op_meta3 = op_metas.get("meta3", 0)

        departamentos.append(
            {
                "nome": "Operacional",
                "meta1": format_currency(op_meta1),
                "meta2": format_currency(op_meta2),
                "meta3": format_currency(op_meta3),
                "pct_meta1": (liq_operacional / op_meta1 * 100) if op_meta1 > 0 else 0,
                "pct_meta2": (liq_operacional / op_meta2 * 100) if op_meta2 > 0 else 0,
                "pct_meta3": (liq_operacional / op_meta3 * 100) if op_meta3 > 0 else 0,
                "realizado": format_currency(liq_operacional),
                "percent": format_percent((liq_operacional / op_meta1 * 100) if op_meta1 > 0 else 0),
            }
        )

        # Outros departamentos com repasse e líquido por departamento
        for nome, tabela, prefixo in departamentos_config:
            metas = self.fetch_metas_departamento(tabela, prefixo)

            # Tecnologia usa PJ como chave no dicionário de realizados/repasses
            key_realizado = "PJ" if nome == "Tecnologia" else nome
            real = realizados.get(key_realizado, 0)
            valor_repasse = repasses.get(key_realizado, 0)
            valor_liquido = liquido.get(key_realizado, 0)

            meta1 = metas.get("meta1", 0)
            meta2 = metas.get("meta2", 0)
            meta3 = metas.get("meta3", 0)

            # Exibe Realizado bruto no mini card (pois mostrará o repasse depois), mas bate percentuais via Líquido
            departamentos.append(
                {
                    "nome": nome,
                    "meta1": format_currency(meta1),
                    "meta2": format_currency(meta2),
                    "meta3": format_currency(meta3),
                    "pct_meta1": (valor_liquido / meta1 * 100) if meta1 > 0 else 0,
                    "pct_meta2": (valor_liquido / meta2 * 100) if meta2 > 0 else 0,
                    "pct_meta3": (valor_liquido / meta3 * 100) if meta3 > 0 else 0,
                    "realizado": format_currency(real),
                    "repasse": format_currency(valor_repasse),
                    "liquido": format_currency(valor_liquido),
                    "percent": format_percent((valor_liquido / meta1 * 100) if meta1 > 0 else 0),
                }
            )

        # Formatar receitas
        receitas = {
            "outras": format_currency(receitas_raw.get("outras", 0)),
            "intercompany": format_currency(receitas_raw.get("intercompany", 0)),
            "repasse_total": format_currency(repasses.get("Total", 0)),
            "sem_categoria": format_currency(receitas_raw.get("sem_categoria", 0)),
        }

        logger.info(f"OK - Dados de {len(departamentos)} departamentos obtidos")
        return total_gs, departamentos, receitas


# Teste
if __name__ == "__main__":
    fetcher = PowerBIDataFetcher()
    total, deps, receitas = fetcher.fetch_all_data()

    print("\n" + "=" * 60)
    print("TOTAL GS:")
    print(json.dumps(total, indent=2, ensure_ascii=False))

    print("\nRECEITAS:")
    print(json.dumps(receitas, indent=2, ensure_ascii=False))

    print("\nDEPARTAMENTOS:")
    for d in deps:
        print(f"\n{d['nome']}:")
        print(f"  Meta1: {d['meta1']}")
        print(f"  Meta2: {d['meta2']}")
        print(f"  Meta3: {d['meta3']}")
        print(f"  Realizado: {d['realizado']}")
        print(f"  %: {d['percent']}")
