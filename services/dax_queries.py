"""
Centralized DAX Queries for Power BI Data Fetching.
Separating queries from logic makes it easier to maintain and update the semantic model references.
"""

def get_realizado_query(date_start, date_end):
    return f"""
    EVALUATE
    CALCULATETABLE(
        ROW(
            "Comercial", [Comercial_Total],
            "Operacional", [Operacional_Total],
            "Corporate", [Valor_Corporate],
            "Educacao", [Valor_Educacao],
            "Expansao", [Valor_Expansao],
            "Franchising", [Valor_Franchising],
            "PJ", [Valor_PJ],
            "Tax", [valor_Tax]
        ),
        DATESBETWEEN('Calendario'[Date], {date_start}, {date_end})
    )
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
            "SemCategoria", [Valor_Sem_Categoria]
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
