"""
Centralized DAX Queries for Power BI Data Fetching.
Separating queries from logic makes it easier to maintain and update the semantic model references.
"""




def get_metas_com_op_query(date_start, date_end):
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Comercial_Meta1", [Total_Comercial_Meta1],
            "Comercial_Meta2", [Total_Comercial_Meta2],
            "Comercial_Meta3", [Total_Comercial_Meta3],
            "Operacional_Meta1", [Total_Operacional_Meta1],
            "Operacional_Meta2", [Total_Operacional_Meta2],
            "Operacional_Meta3", [Total_Operacional_Meta3]
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """


def get_percentuais_gs_query(date_start, date_end):
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Pct_Meta1", [% Meta 1 GS],
            "Pct_Meta2", [% Meta 2 GS],
            "Pct_Meta3", [% Meta 3 GS]
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """


def get_percentuais_com_op_query(date_start, date_end):
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Com_Pct1", [% Meta 1 COMERCIAL],
            "Com_Pct2", [% Meta 2 COMERCIAL],
            "Com_Pct3", [% Meta 3 COMERCIAL],
            "Op_Pct1", [% Meta 1 OPERACIONAL],
            "Op_Pct2", [% Meta 2 OPERACIONAL],
            "Op_Pct3", [% Meta 3 OPERACIONAL]
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """


def get_receitas_query(date_start, date_end):
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "OutrasReceitas", [Valor_OutrasReceitas],
            "InterCompany", [Valor_InterCompany],
            "NaoIdentificada", [Valor_NaoIdentificada],
            "SemCategoria", [Valor_Sem_Categoria],
            "Repasse", [total_repasse],
            "TotalGeral", (
                COALESCE([total_repasse], 0) +
                COALESCE([tax_liquido], 0) +
                COALESCE([corporate_liquido], 0) +
                COALESCE([educacao_liquido], 0) +
                COALESCE([expansao_liquido], 0) +
                COALESCE([franchising_liquido], 0) +
                COALESCE([tecnlogia_liquido], 0) +
                COALESCE([Valor_OutrasReceitas], 0)
            )
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """


def get_metas_dept_query(tabela, month_filter):
    return f"""
    EVALUATE
    FILTER(
        '{tabela}',
        '{tabela}'[Mês] = {month_filter}
    )
    """


def get_percentuais_dept_query(prefixo, date_start, date_end):
    # Se tecnologia, bota 0 nas metas que estão quebradas no PBI
    if prefixo == "Tecnologia":
        return f"""
        EVALUATE
        CALCULATETABLE(
            ROW(
                "Pct1", 0,
                "Pct2", 0,
                "Pct3", 0
            ),
            DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
        )
        """

    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Pct1", [% Meta 1 {prefixo}],
            "Pct2", [% Meta 2 {prefixo}],
            "Pct3", [% Meta 3 {prefixo}]
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """




def get_receitas_liquido_query(date_start, date_end):
    # Líquido = Realizado - Repasse por departamento
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Corporate_Liquido", COALESCE([corporate_liquido], 0),
            "Educacao_Liquido", COALESCE([educacao_liquido], 0),
            "Expansao_Liquido", COALESCE([expansao_liquido], 0),
            "Franchising_Liquido", COALESCE([franchising_liquido], 0),
            "Tax_Liquido", COALESCE([tax_liquido], 0),
            "Tecnologia_Liquido", COALESCE([tecnlogia_liquido], 0),
            "Total_Comercial", COALESCE([total_liquido_comercial], 0),
            "Total_Operacao", COALESCE([total_liquido_operacao], 0),
            "Corporate_Repasse", COALESCE([Valor_Corporate_Repasse], 0),
            "Tax_Repasse", COALESCE([valor_Tax_Repasse], 0),
            "Educacao_Repasse", COALESCE([Valor_Educacao_Repasse], 0),
            "Expansao_Repasse", COALESCE([Valor_Expansao_Repasse], 0),
            "Franchising_Repasse", COALESCE([Valor_Franchising_Repasse], 0),
            "Tecnologia_Repasse", COALESCE([Valor_PJ_Repasse], 0)
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
    """


