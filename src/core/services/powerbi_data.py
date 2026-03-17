"""
Serviço de Dados Power BI.
Responsável por buscar dados reais de metas e receitas do Power BI via DAX,
integrando diretamente com o modelo semântico mapeado.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from src.config import POWERBI_CONFIG
from src.core.clients.powerbi_client import PowerBIClient
from src.core.services.dax_queries import (
    get_metas_com_op_query,
    get_metas_dept_query,
    get_percentuais_com_op_query,
    get_percentuais_dept_query,
    get_percentuais_gs_query,
    get_receitas_liquido_query,
    get_receitas_query,
)
from src.core.utils.logger import get_logger

logger = get_logger("powerbi_data")

# Configuração dos departamentos: (nome_exibição, tabela_metas, prefixo_medidas)
_DEPARTAMENTOS_CONFIG: list[tuple[str, str, str]] = [
    ("Corporate", "Corporate_Metas", "CORPORATE"),
    ("Educação", "Educação_Metas", "EDUCACAO"),
    ("Expansão", "Expansão_Metas", "EXPANSAO"),
    ("Franchising", "Franchising_Metas", "FRANCHISING"),
    ("Tax", "TAX_Metas", "TAX"),
    ("Tecnologia", "PJ360_Metas", "PJ"),
]


def format_currency(value) -> str:
    """Formata valor como moeda brasileira."""
    if value is None or value == 0:
        return "-"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value) -> str:
    """Formata valor como percentual."""
    if value is None or value == 0:
        return ""
    return f"{value:.2f}%".replace(".", ",")


class PowerBIDataFetcher:
    """
    Classe responsável por buscar dados de metas do Power BI via consultas DAX.
    Gerencia autenticação e orquestra as chamadas para diferentes tabelas e medidas.
    """

    def __init__(self):
        self.client = PowerBIClient(
            workspace_id=POWERBI_CONFIG.get("metas_workspace_id"),
            dataset_id=POWERBI_CONFIG.get("metas_dataset_id"),
        )
        self._authenticated = False

    def authenticate(self) -> bool:
        """Realiza a autenticação no Power BI se ainda não estiver autenticado."""
        if not self._authenticated:
            self._authenticated = self.client.authenticate()
        return self._authenticated

    def _get_month_filter(self) -> str:
        """Retorna filtro DAX DATE() para o primeiro dia do mês atual."""
        now = datetime.now()
        return f"DATE({now.year}, {now.month}, 1)"

    def _get_month_range(self) -> tuple[str, str]:
        """Retorna (start_str, end_str) no formato DAX DATE() para o mês atual."""
        now = datetime.now()
        start = datetime(now.year, now.month, 1)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
        start_str = f"DATE({start.year}, {start.month}, {start.day})"
        end_str = f"DATE({end.year}, {end.month}, {end.day})"
        return start_str, end_str

    def fetch_valores_realizados(self) -> dict:
        """Busca os valores REALIZADOS de cada departamento (da tabela Medidas)."""
        start_str, end_str = self._get_month_range()
        query = get_receitas_liquido_query(start_str, end_str)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "Comercial": row.get("[Total_Comercial]") or 0,
                    "Operacional": row.get("[Total_Operacao]") or 0,
                    "Corporate": row.get("[Corporate_Liquido]") or 0,
                    "Educação": row.get("[Educacao_Liquido]") or 0,
                    "Expansão": row.get("[Expansao_Liquido]") or 0,
                    "Franchising": row.get("[Franchising_Liquido]") or 0,
                    "Tecnologia": row.get("[Tecnologia_Liquido]") or 0,
                    "Tax": row.get("[Tax_Liquido]") or 0,
                    # Repasses individuais
                    "Corporate_Repasse": row.get("[Corporate_Repasse]") or 0,
                    "Educação_Repasse": row.get("[Educacao_Repasse]") or 0,
                    "Expansão_Repasse": row.get("[Expansao_Repasse]") or 0,
                    "Franchising_Repasse": row.get("[Franchising_Repasse]") or 0,
                    "Tax_Repasse": row.get("[Tax_Repasse]") or 0,
                    "Tecnologia_Repasse": row.get("[Tecnologia_Repasse]") or 0,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar valores realizados: {e}")

        return {}

    def fetch_metas_comercial_operacional(self) -> dict:
        """Busca as METAS específicas de Comercial e Operacional com filtro de data."""
        start_str, end_str = self._get_month_range()
        query = get_metas_com_op_query(start_str, end_str)

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

    def fetch_percentuais_gs(self) -> dict:
        """Busca percentuais das metas GS (% Meta 1/2/3 GS)."""
        start_str, end_str = self._get_month_range()
        query = get_percentuais_gs_query(start_str, end_str)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "pct_meta1": (row.get("[Pct_Meta1]") or 0) * 100,
                    "pct_meta2": (row.get("[Pct_Meta2]") or 0) * 100,
                    "pct_meta3": (row.get("[Pct_Meta3]") or 0) * 100,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar percentuais GS: {e}")

        return {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0}

    def fetch_percentuais_comercial_operacional(self) -> dict:
        """Busca percentuais de Comercial e Operacional."""
        start_str, end_str = self._get_month_range()
        query = get_percentuais_com_op_query(start_str, end_str)

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

    def fetch_receitas(self) -> dict:
        """Busca valores de receitas (Outras Receitas, Intercompany, etc.)."""
        start_str, end_str = self._get_month_range()
        query = get_receitas_query(start_str, end_str)

        try:
            result = self.client.execute_dax(query)
            if result and len(result) > 0:
                row = result[0]
                return {
                    "outras": row.get("[OutrasReceitas]") or 0,
                    "intercompany": row.get("[InterCompany]") or 0,
                    "total_geral": row.get("[TotalGeral]") or 0,
                    "repasse": row.get("[Repasse]") or 0,
                    "sem_categoria": row.get("[SemCategoria]") or 0,
                }
        except Exception as e:
            logger.error(f"Erro ao buscar receitas: {e}")

        return {"outras": 0, "intercompany": 0, "total_geral": 0, "repasse": 0, "sem_categoria": 0}

    def fetch_metas_departamento(self, tabela: str, prefixo: str) -> dict:
        """Busca metas de um departamento específico."""
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

    def fetch_percentuais_departamento(self, prefixo: str) -> dict:
        """Busca percentuais de atingimento de metas para um departamento."""
        start_str, end_str = self._get_month_range()
        query = get_percentuais_dept_query(prefixo, start_str, end_str)

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

    def fetch_all_data(self) -> tuple[dict | None, list | None, dict | None]:
        """
        Orquestra a busca de TODOS os dados necessários para a automação.

        Executa as 18 consultas DAX em paralelo (ThreadPoolExecutor) em vez de
        sequencialmente, reduzindo o tempo total de ~9 minutos para ~1 minuto.

        Retorna:
            - total_gs: Relatório consolidado da GS.
            - departamentos: Lista de relatórios por departamento.
            - receitas: Dados de outras receitas/intercompany.
        """
        if not self.authenticate():
            logger.error("Falha na autenticação com Power BI")
            return None, None, None

        logger.info("Buscando dados do Power BI em paralelo...")

        # Monta a lista de todas as tarefas independentes como (chave, função, args)
        tasks: list[tuple[str, object, tuple]] = [
            ("realizados", self.fetch_valores_realizados, ()),
            ("receitas_raw", self.fetch_receitas, ()),
            ("metas_gs", self.fetch_metas_departamento, ("GS_Metas", "GS")),
            ("pct_gs", self.fetch_percentuais_gs, ()),
            ("metas_com_op", self.fetch_metas_comercial_operacional, ()),
            ("pct_com_op", self.fetch_percentuais_comercial_operacional, ()),
        ]

        for nome, tabela, prefixo in _DEPARTAMENTOS_CONFIG:
            tasks.append((f"metas_{nome}", self.fetch_metas_departamento, (tabela, prefixo)))
            tasks.append((f"pct_{nome}", self.fetch_percentuais_departamento, (prefixo,)))

        # Executa todas as queries DAX em paralelo — max_workers limitado a 10
        # para não sobrecarregar a API do Power BI
        results: dict = {}
        with ThreadPoolExecutor(max_workers=min(len(tasks), 10)) as executor:
            future_to_key = {executor.submit(fn, *args): key for key, fn, args in tasks}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Erro em query paralela '{key}': {e}")
                    results[key] = {}

        # --- Monta estrutura de retorno ---
        realizados = results.get("realizados", {})
        receitas_raw = results.get("receitas_raw", {})
        metas_gs = results.get("metas_gs", {"meta1": 0, "meta2": 0, "meta3": 0})
        pct_gs = results.get("pct_gs", {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0})
        metas_com_op = results.get("metas_com_op", {})
        pct_com_op = results.get("pct_com_op", {})

        real_comercial = realizados.get("Comercial", 0)
        real_operacional = realizados.get("Operacional", 0)
        realizado_gs = real_comercial + real_operacional

        total_gs = {
            "meta1": format_currency(metas_gs.get("meta1", 0)),
            "meta2": format_currency(metas_gs.get("meta2", 0)),
            "meta3": format_currency(metas_gs.get("meta3", 0)),
            "pct_meta1": pct_gs.get("pct_meta1", 0),
            "pct_meta2": pct_gs.get("pct_meta2", 0),
            "pct_meta3": pct_gs.get("pct_meta3", 0),
            "realizado": format_currency(realizado_gs),
            "percent": format_percent(pct_gs.get("pct_meta1", 0)),
        }

        departamentos: list[dict] = []

        # Comercial — usa percentuais do Power BI
        com_metas = metas_com_op.get("Comercial", {})
        com_pct = pct_com_op.get("Comercial", {})
        departamentos.append(
            {
                "nome": "Comercial",
                "meta1": format_currency(com_metas.get("meta1", 0)),
                "meta2": format_currency(com_metas.get("meta2", 0)),
                "meta3": format_currency(com_metas.get("meta3", 0)),
                "pct_meta1": com_pct.get("pct_meta1", 0),
                "pct_meta2": com_pct.get("pct_meta2", 0),
                "pct_meta3": com_pct.get("pct_meta3", 0),
                "realizado": format_currency(real_comercial),
                "percent": format_percent(com_pct.get("pct_meta1", 0)),
            }
        )

        # Operacional — usa percentuais do Power BI
        op_metas = metas_com_op.get("Operacional", {})
        op_pct = pct_com_op.get("Operacional", {})
        departamentos.append(
            {
                "nome": "Operacional",
                "meta1": format_currency(op_metas.get("meta1", 0)),
                "meta2": format_currency(op_metas.get("meta2", 0)),
                "meta3": format_currency(op_metas.get("meta3", 0)),
                "pct_meta1": op_pct.get("pct_meta1", 0),
                "pct_meta2": op_pct.get("pct_meta2", 0),
                "pct_meta3": op_pct.get("pct_meta3", 0),
                "realizado": format_currency(real_operacional),
                "percent": format_percent(op_pct.get("pct_meta1", 0)),
            }
        )

        # Outros departamentos — resultados já disponíveis no dict paralelo
        for nome, _tabela, _prefixo in _DEPARTAMENTOS_CONFIG:
            metas = results.get(f"metas_{nome}", {"meta1": 0, "meta2": 0, "meta3": 0})
            pct = results.get(f"pct_{nome}", {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0})
            liquido_val = realizados.get(nome, 0)
            repasse_val = realizados.get(f"{nome}_Repasse", 0)

            departamentos.append(
                {
                    "nome": nome,
                    "meta1": format_currency(metas.get("meta1", 0)),
                    "meta2": format_currency(metas.get("meta2", 0)),
                    "meta3": format_currency(metas.get("meta3", 0)),
                    "pct_meta1": pct.get("pct_meta1", 0),
                    "pct_meta2": pct.get("pct_meta2", 0),
                    "pct_meta3": pct.get("pct_meta3", 0),
                    "realizado": format_currency(liquido_val + repasse_val),  # Total Bruto
                    "repasse": format_currency(repasse_val),
                    "liquido": format_currency(liquido_val),
                    "percent": format_percent(pct.get("pct_meta1", 0)),
                }
            )

        receitas = {
            "outras": format_currency(receitas_raw.get("outras", 0)),
            "intercompany": format_currency(receitas_raw.get("intercompany", 0)),
            "repasse": format_currency(receitas_raw.get("repasse", 0)),
            "total_geral": format_currency(receitas_raw.get("total_geral", 0)),
            "sem_categoria": format_currency(receitas_raw.get("sem_categoria", 0)),
        }

        logger.info(f"OK - Dados de {len(departamentos)} departamentos obtidos em paralelo")
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
    if deps:
        for d in deps:
            print(f"\n{d['nome']}:")
            print(f"  Meta1: {d['meta1']}")
            print(f"  Meta2: {d['meta2']}")
            print(f"  Meta3: {d['meta3']}")
            print(f"  Realizado: {d['realizado']}")
            print(f"  %: {d['percent']}")
