import re
from typing import Any, Dict, List

from src.core.services.dax_queries import get_unidades_list_query, get_unidades_summary_query
from src.core.utils.logger import get_logger

logger = get_logger(__name__)


def _normalize_keys(row: Dict) -> Dict:
    """
    Remove prefixo de tabela e colchetes dos nomes de colunas retornados pela API do Power BI.
    Ex: "[FatoUnidades].[Nome]" → "Nome" | "[NovasUnidades]" → "NovasUnidades"
    """
    return {re.sub(r".*\[|\]", "", k).strip(): v for k, v in row.items()}


def _extract_numeric(v: Any) -> int:
    """
    Extrai valor numérico de retornos do Power BI.
    Suporta: int/float diretos, strings, e HTML de medidas customizadas
    (ex: <div class='kpiValue'>31</div>).
    """
    if isinstance(v, (int, float)):
        return int(v)

    if not isinstance(v, str):
        return 0

    # Tenta extrair de divs HTML (kpiValue, cardValor, etc.)
    match_html = re.search(
        r"<div[^>]*class=['\"](?:kpiValue|cardValor|kpiContainer)['\"][^>]*>\s*([\d.,]+)\s*</div>",
        v,
        re.DOTALL | re.IGNORECASE,
    )
    if match_html:
        raw = match_html.group(1).replace(".", "").replace(",", "")
        return int(raw) if raw.isdigit() else 0

    # Fallback: extrai primeiro número da string
    match_num = re.search(r"\d+", re.sub(r"<[^>]+>", "", v))
    if match_num:
        return int(match_num.group(0))

    return 0


class PowerBIUnidadesFetcher:
    """
    Fetcher especializado para o dataset de Unidades do Power BI.
    """

    def __init__(self, client):
        self.client = client

    def fetch_summary(self, date_start: str, date_end: str) -> Dict:
        """
        Busca o resumo (medidas KPI) para o dashboard de unidades via Power BI DAX.
        Normaliza chaves e extrai valores numéricos de HTML se necessário.
        """
        summary_query = get_unidades_summary_query(date_start, date_end)
        rows = self.client.execute_dax(summary_query)

        summary_data = {
            "novas_unidades": 0,
            "unidades_pagantes": 0,
            "unidades_inativadas": 0,
        }

        if rows:
            row = _normalize_keys(rows[0])
            logger.debug(f"Summary keys normalizadas: {list(row.keys())}")

            summary_data = {
                "novas_unidades": _extract_numeric(row.get("NovasUnidades", 0)),
                "unidades_pagantes": _extract_numeric(row.get("UnidadesPagantes", 0)),
                "unidades_inativadas": _extract_numeric(row.get("UnidadesInativadas", 0)),
            }
            logger.info(f"Summary: {summary_data}")

        return summary_data

    def fetch_units_list(self, date_start: str, date_end: str, status: str) -> List[Dict]:
        """
        Busca a lista de unidades (novas ou inativadas) via Power BI DAX.
        Normaliza as chaves de cada item retornado.
        """
        query = get_unidades_list_query(date_start, date_end, status=status)
        rows = self.client.execute_dax(query)

        if not rows:
            return []

        normalized = [_normalize_keys(row) for row in rows]
        logger.debug(
            f"fetch_units_list ({status}): {len(normalized)} itens, "
            f"keys: {list(normalized[0].keys()) if normalized else []}"
        )
        return normalized

    def fetch_dashboard_data(self, date_start: str, date_end: str) -> Dict:
        """Busca todos os dados necessários para o dashboard de unidades."""
        summary = self.fetch_summary(date_start, date_end)
        new_units = self.fetch_units_list(date_start, date_end, status="Nova")
        inactive_units = self.fetch_units_list(date_start, date_end, status="Inativada")

        # As medidas KPI do Power BI não respondem bem a filtros de período curto.
        # Os contadores são derivados diretamente das listas para garantir consistência.
        summary["novas_unidades"] = len(new_units)
        summary["unidades_inativadas"] = len(inactive_units)

        return {
            "summary": summary,
            "new_units_list": new_units,
            "inactive_units_list": inactive_units,
        }
