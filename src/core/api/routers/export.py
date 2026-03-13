import calendar
import io
import logging
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.services.supabase_service import SupabaseService

logger = logging.getLogger("api_export")
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Mapeamento de número do mês para nome em português
MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

# Ordem de exibição das abas — Departamentos de Metas + Receitas
DEPT_ORDER = ["Expansão", "Franchising", "Educação", "Tax", "Corporate", "Tecnologia"]
RECEITAS_ORDER = ["Intercompany", "Repasse", "Sem Categoria", "Outras Receitas"]

# Colunas a buscar e seus nomes amigáveis no Excel
COL_MAP = {
    "codigo": "Codigo",
    "descricao": "Categoria",
    "data_emissao": "Emissão",
    "razao_social": "Cliente",
    "valor": "Valor",
    "data_vencimento": "Pagamento",
    "bandeira": "Empresa",
}

# Ordem das colunas conforme visualização no Power BI
COL_ORDER = ["Codigo", "Categoria", "Emissão", "Cliente", "Valor", "Pagamento", "Empresa"]

# ─── Mapeamento Categoria → Departamento ─────────────────────────────────────
# Matching case-insensitive por substring; a ordem importa (mais específico primeiro)
DEPT_KEYWORDS: dict[str, list[str]] = {
    # ── Departamentos de Metas ──────────────────────────────────────
    "Tecnologia": [
        "licenças de softwares e programas auditatax",
        "licenças de softwares e programas auditacard",
        "receita auditacard",
    ],
    "Expansão": [
        "receita de taxas de franquia/aliança",
        "receita de taxa de franquia/aliança",
        "receita de franquia/aliança",
        "taxas de franquia/aliança",
        "expansão - taxa de franquia",
        "expansão - taxa de licenciamento",
        "expansão - taxa de treinamento",
        "licenças de softwares e programas pj360",
        "clientes - licenças de softwares e programas pj360",
        "receita de implantação",
        "licenciados - taxa de adesão",
    ],
    "Franchising": [
        "receita de royalties/crm",
        "receita de royalties variáveis",
        "receita de royalties antecipado",
        "receita de royalties",
        "royalties/crm",
        "royalties variáveis",
        "royalties antecipado",
        "receita de crm",
        "franchising - crm",
        "franchising - royalties",
        "fundo de marketing",
    ],
    "Educação": [
        "receita de treinamento interno",
        "receita de treinamento externo",
        "receita de treinamento",
        "receita de treinamentos",
        "treinamento e eventos",
    ],
    "Tax": [
        "receita de prt",
        "receita de pontos qualificados",
        "receita de ponto qualificados",
        "clientes - tributário",
        "clientes - transação tributária",
        "receita de transação tributária",
        "receita de projetos especiais",
        "receita de teses",
        "receita de mapa fiscal",
        "receita de gestão do passivo tributário",
        "receita de revisão previdenciária",
        "receita de consultivo de processos",
        "êxito de sucumbência",
    ],
    "Corporate": [
        "receita de valuation",
        "receita de serviço jurídico",
        "receita de serviços jurídicos",
        "receita da serviços jurídicos",
        "receita de serviços juridicos",
        "receita de serviços contábeis",
        "receita de serviços contabeis",
        "receita de seguros",
        "receita de renegociação de dívidas",
        "receita de mea",
        "receita de liquidação",
        "receita de holding itbi",
        "receita de holding governança",
        "receita de holding",
        "clientes - holding",
        "receita de gestão de mercado livre de energia",
        "receita de mercado livre de energia",
        "receita de mercado livre",
        "receita de financiamento de franquia",
        "receita de energy assessoria",
        "receita de energy geração",
        "receita de recupera energia",
        "receita de assinatura de energia",
        "adiantamento de mercado livre",
        "receita de contabilidade recorrente",
        "receita de consultoria estratégica",
        "receita de cessão/negociação de precatórios",
        "receita de captação de recursos",
        "receita de ajuizamento",
        "receita de aje",
        "clientes - intermediações de negócios",
        "clientes - licenças de softwares e programas auditacard",
        "clientes - licenças de softwares e programas externo",
        "clientes - licenças de softwares e programas gs",
        "clientes - licenças de softwares e programas",
        "licenças de softwares e programas",
        "bpo financeiro",
        "operação - bpo financeiro",
        "receita de bpo",
        "receita de avaliação patrimonial",
        "receita de marca",
        "receita de marketing",
        "receita de suporte e consultoria em ti",
        "clientes - locação de equipamentos e suporte ti",
        "clientes - e-mails",
        "clientes - saf",
        "clientes - desossa",
        "clientes - taxa setup",
        "serviços administrativos",
        "operação - auditarcard",
        "operação - auditacard",
        "receita de operação de jobs",
        "receita de operação de job",
        "operação de jobs",
        "receita dho",
    ],
    # ── Receitas ────────────────────────────────────────────────────
    "Intercompany": [
        "mutuo - entre empresas",
        "mutuo - empresas grupo",
        "receita de empréstimos entre empresas",
        "receita de transferência entre empresas do grupo",
        "aplicação para empréstimos",
        "capital de giro",
        "aporte de capital",
        "integralização de capital",
        "antecipação de lucros",
        "distribuição de lucros",
        "devolução de capital de giro",
        "receita de antecipação de recebíveis",
        "receita de financiamento - rendimento de financiamento",
        "receita de financiamento - amortização de crédito",
        "amortização de credito",
    ],
    "Repasse": [
        "adiantamento - repasse",
        "adiantamento para repasse",
        "adiantamento para repasses",
        "adiantamento de projeto",
        "adiantamento de despesa",
        "adiantamento de clientes",
        "adiantamento feira",
        "adiantamento",
        "repasse comercial",
        "repasse marca",
        "repasse",
    ],
    "Sem Categoria": [
        "receita a identificar",
        "a identificar",
        "receita importação financeiro gs",
        "receita da conta operacional",
        "receita da conta studio fiscal",
    ],
    "Outras Receitas": [
        "rendimento de aplicação financeira",
        "rendimento de aplicações",
        "rendimentos financiamentos",
        "rendimentos de aplicações",
        "juros ativos",
        "receita de locação de espaço",
        "receita de coworking",
        "receita de estacionamento",
        "receita de compensação",
        "receita de retificação",
        "receita de restituição",
        "receita de recuperação",
        "recuperação de despesas",
        "reembolso de despesas",
        "devolução de pagamentos feitos",
        "devolução pagamento efetuado",
        "devolução de pagamento efetuado",
        "devolução de serviço prestado",
        "devolução de pagamento feito",
        "devoluções de compra de suprimentos",
        "receita de valores a transferir",
        "valores a transferir",
        "receita de loja",
        "produtos/loja",
        "receita de produtos/loja",
        "receita eventos",
        "receita de marketing",
        "receita de estacionamento",
        "estornos",
        "descontos obtidos",
        "receita de serviços de impressão",
        "receita de suporte",
        "receita de locação",
        "adiantamento de mercado livre",
        "venda de itens obsoletos",
    ],
}


def classificar_departamento(descricao: str | None) -> str | None:
    """
    Classifica a categoria (descricao) em departamento ou aba de Receita.
    Usa matching case-insensitive por substring. Retorna None se não mapeada.
    """
    if not descricao:
        return None
    descricao_lower = descricao.lower().strip()
    for dept, keywords in DEPT_KEYWORDS.items():
        for kw in keywords:
            if kw in descricao_lower:
                return dept
    return None


@router.get("/metas")
@limiter.limit("30/minute")
async def export_metas_excel(
    request: Request,
    mes: int = Query(default=None, description="Número do mês (1-12). Omitir para exportar todo o histórico."),
    ano: int = Query(default=None, description="Ano (ex: 2026). Obrigatório se mes for informado."),
):
    """
    Exporta dados de Contas a Receber (Metas) do Supabase para Excel.
    - Sem parâmetros: exporta todo o histórico disponível.
    - Com mes+ano: exporta apenas o mês/ano especificado.
    Gera aba 'Todos' + abas por Departamento + abas de Receitas.
    """
    hoje = datetime.now()
    ano_ref = ano or hoje.year
    mes_nome = MESES_PT.get(mes, "Histórico") if mes else "Histórico Completo"

    try:
        svc = SupabaseService()

        # Monta filtros de data como lista de tuplas para suportar params repetidos (gte+lte)
        filtros_data: list[tuple] = []
        if mes:
            ano_ref = ano or hoje.year
            mes_str = f"{mes:02d}"
            # calendar.monthrange suporta anos bissextos automaticamente
            ultimo_dia = calendar.monthrange(ano_ref, mes)[1]
            data_inicio = f"{ano_ref}-{mes_str}-01"
            data_fim = f"{ano_ref}-{mes_str}-{ultimo_dia:02d}"
            # Ambos os limites enviados ao Supabase como params separados
            filtros_data = [
                ("data_emissao", f"gte.{data_inicio}"),
                ("data_emissao", f"lte.{data_fim}"),
            ]

        # Busca paginada do Supabase
        all_rows = []
        offset = 0
        limit = 1000

        while True:
            # Monta params como lista de tuplas preservando os filtros de data repetidos.
            # prefer_count_none=True evita o COUNT(*) auxiliar do PostgREST em cada página,
            # reduzindo o tempo de resposta em loops de paginação grandes.
            p: list[tuple] = [
                ("select", ",".join(COL_MAP.keys())),
                ("order", "descricao.asc,razao_social.asc"),
                ("offset", offset),
                ("limit", limit),
                *filtros_data,
            ]
            chunk = svc._get("nexus_contas_receber", p, prefer_count_none=True)
            if not chunk:
                break
            all_rows.extend(chunk)
            if len(chunk) < limit:
                break
            offset += limit

        if not all_rows:
            detalhe = f"{mes_nome}/{ano_ref}" if mes else "histórico completo"
            raise HTTPException(status_code=404, detail=f"Nenhum dado encontrado para {detalhe}")

        # Classifica cada linha com o departamento
        sem_classificacao: set[str] = set()
        for row in all_rows:
            descricao = row.get("descricao")
            dept = classificar_departamento(descricao)
            row["_dept"] = dept
            if dept is None:
                sem_classificacao.add(descricao or "(em branco)")

        if sem_classificacao:
            logger.warning(
                f"Categorias sem departamento mapeado ({len(sem_classificacao)}): {sorted(sem_classificacao)}"
            )

        # Converte para DataFrame e renomeia colunas
        df = pd.DataFrame(all_rows)
        df.rename(columns={k: v for k, v in COL_MAP.items() if k in df.columns}, inplace=True)

        # Formata datas para padrão BR
        for date_col in ["Emissão", "Pagamento"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%d/%m/%Y")

        # Colunas finais do Excel
        existing_cols = [c for c in COL_ORDER if c in df.columns]

        # Gera o Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Aba "Todos" com todas as linhas
            df[existing_cols].to_excel(writer, sheet_name="Todos", index=False)

            # Abas por departamento de Metas (na ordem do painel)
            for dept_name in DEPT_ORDER:
                dept_df = df[df["_dept"] == dept_name]
                if dept_df.empty:
                    continue
                dept_df[existing_cols].to_excel(writer, sheet_name=dept_name[:31], index=False)

            # Abas de Outras Receitas
            for receita_name in RECEITAS_ORDER:
                rec_df = df[df["_dept"] == receita_name]
                if rec_df.empty:
                    continue
                rec_df[existing_cols].to_excel(writer, sheet_name=receita_name[:31], index=False)

            # Aba residual para categorias ainda sem classificação
            classificados = set(DEPT_ORDER) | set(RECEITAS_ORDER)
            outros_df = df[~df["_dept"].isin(classificados) | df["_dept"].isna()]
            if not outros_df.empty:
                outros_df[existing_cols].to_excel(writer, sheet_name="Outros", index=False)

        output.seek(0)
        if mes:
            filename = f"Metas_Detalhado_{mes_nome}_{ano_ref}.xlsx"
        else:
            filename = "Metas_Detalhado_Historico_Completo.xlsx"

        # Retorna o arquivo e loga as categorias não mapeadas como aviso
        response = StreamingResponse(
            output,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        if sem_classificacao:
            logger.warning(
                f"[EXPORT] {len(sem_classificacao)} categorias sem departamento foram para aba 'Outros': "
                + ", ".join(sorted(sem_classificacao))
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na exportação de Metas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
