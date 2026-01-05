"""
Busca dados reais de metas do Power BI
Integra com o modelo semântico mapeado
"""
import json
from datetime import datetime, timedelta
from powerbi_client import PowerBIClient


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


class PowerBIDataFetcher:
    """Busca dados de metas do Power BI via DAX"""
    
    def __init__(self):
        self.client = PowerBIClient()
        self._authenticated = False
    
    def authenticate(self):
        """Autentica no Power BI"""
        if not self._authenticated:
            self._authenticated = self.client.authenticate()
        return self._authenticated
    
    def _get_month_filter(self):
        """Retorna filtro de data para o mês atual"""
        now = datetime.now()
        return f"DATE({now.year}, {now.month}, 1)"
    
    def fetch_valores_realizados(self):
        """Busca valores realizados de cada departamento (da tabela Medidas)"""
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        # Calcular último dia do mês
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            
        date_filter_start = f"DATE({start_date.year}, {start_date.month}, {start_date.day})"
        date_filter_end = f"DATE({end_date.year}, {end_date.month}, {end_date.day})"
        
        # Filtra a tabela Calendario pelo período selecionado
        # Isso deve propagar para ContasReceber[data_pagamento] se houver relacionamento
        query = f"""
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
            DATESBETWEEN('Calendario'[Date], {date_filter_start}, {date_filter_end})
        )
        """
        
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
            print(f"Erro ao buscar valores realizados: {e}")
        
        return {}
    
    def fetch_metas_comercial_operacional(self):
        """Busca metas de Comercial e Operacional (da tabela Medidas)"""
        query = """
        EVALUATE
        ROW(
            "Comercial_Meta1", [Total_Comercial_Meta1],
            "Comercial_Meta2", [Total_Comercial_Meta2],
            "Comercial_Meta3", [Total_Comercial_Meta3],
            "Operacional_Meta1", [Total_Operacional_Meta1],
            "Operacional_Meta2", [Total_Operacional_Meta2],
            "Operacional_Meta3", [Total_Operacional_Meta3]
        )
        """
        
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
                    }
                }
        except Exception as e:
            print(f"Erro ao buscar metas Comercial/Operacional: {e}")
        
        return {}
    
    def fetch_metas_departamento(self, tabela, prefixo):
        """Busca metas de um departamento específico"""
        month_filter = self._get_month_filter()
        
        query = f"""
        EVALUATE
        FILTER(
            '{tabela}',
            '{tabela}'[Mês] = {month_filter}
        )
        """
        
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
            print(f"Erro ao buscar metas {tabela}: {e}")
        
        return {"meta1": 0, "meta2": 0, "meta3": 0}
    
    def fetch_all_data(self):
        """Busca todos os dados necessários para a automação"""
        if not self.authenticate():
            print("Falha na autenticação com Power BI")
            return None, None
        
        print("Buscando dados do Power BI...")
        
        # 1. Buscar valores realizados
        realizados = self.fetch_valores_realizados()
        
        # 2. Buscar metas GS (total)
        metas_gs = self.fetch_metas_departamento("GS_Metas", "GS")
        
        # 3. Buscar metas Comercial/Operacional
        metas_com_op = self.fetch_metas_comercial_operacional()
        
        # 4. Buscar metas dos outros departamentos
        departamentos_config = [
            ("Corporate", "Corporate_Metas", "CORPORATE"),
            ("Educação", "Educação_Metas", "EDUCAÇAO"),
            ("Expansão", "Expansão_Metas", "EXPANSAO"),
            ("Franchising", "Franchising_Metas", "FRANCHISING"),
            ("Tax", "TAX_Metas", "Tax"),
            ("Tecnologia", "PJ360_Metas", "PJ"),
        ]
        
        # Montar dados formatados
        total_gs = {
            "meta1": format_currency(metas_gs.get("meta1", 0)),
            "meta2": format_currency(metas_gs.get("meta2", 0)),
            "meta3": format_currency(metas_gs.get("meta3", 0)),
            "realizado": format_currency(sum(realizados.values())),
            "percent": format_percent(
                (sum(realizados.values()) / metas_gs.get("meta1", 1)) * 100 
                if metas_gs.get("meta1", 0) > 0 else 0
            )
        }
        
        departamentos = []
        
        # Comercial
        com_metas = metas_com_op.get("Comercial", {})
        com_real = realizados.get("Comercial", 0)
        departamentos.append({
            "nome": "Comercial",
            "meta1": format_currency(com_metas.get("meta1", 0)),
            "meta2": format_currency(com_metas.get("meta2", 0)),
            "meta3": format_currency(com_metas.get("meta3", 0)),
            "realizado": format_currency(com_real),
            "percent": format_percent(
                (com_real / com_metas.get("meta1", 1)) * 100 
                if com_metas.get("meta1", 0) > 0 else 0
            )
        })
        
        # Operacional
        op_metas = metas_com_op.get("Operacional", {})
        op_real = realizados.get("Operacional", 0)
        departamentos.append({
            "nome": "Operacional",
            "meta1": format_currency(op_metas.get("meta1", 0)),
            "meta2": format_currency(op_metas.get("meta2", 0)),
            "meta3": format_currency(op_metas.get("meta3", 0)),
            "realizado": format_currency(op_real),
            "percent": format_percent(
                (op_real / op_metas.get("meta1", 1)) * 100 
                if op_metas.get("meta1", 0) > 0 else 0
            )
        })
        
        # Outros departamentos
        for nome, tabela, prefixo in departamentos_config:
            metas = self.fetch_metas_departamento(tabela, prefixo)
            
            # Mapeamento de nome para chave de realizado (Tecnologia -> PJ)
            key_realizado = "PJ" if nome == "Tecnologia" else nome
            real = realizados.get(key_realizado, 0)
            
            departamentos.append({
                "nome": nome,
                "meta1": format_currency(metas.get("meta1", 0)),
                "meta2": format_currency(metas.get("meta2", 0)),
                "meta3": format_currency(metas.get("meta3", 0)),
                "realizado": format_currency(real),
                "percent": format_percent(
                    (real / metas.get("meta1", 1)) * 100 
                    if metas.get("meta1", 0) > 0 else 0
                )
            })
        
        print(f"OK - Dados de {len(departamentos)} departamentos obtidos")
        return total_gs, departamentos


# Teste
if __name__ == "__main__":
    fetcher = PowerBIDataFetcher()
    total, deps = fetcher.fetch_all_data()
    
    print("\n" + "=" * 60)
    print("TOTAL GS:")
    print(json.dumps(total, indent=2, ensure_ascii=False))
    
    print("\nDEPARTAMENTOS:")
    for d in deps:
        print(f"\n{d['nome']}:")
        print(f"  Meta1: {d['meta1']}")
        print(f"  Meta2: {d['meta2']}")
        print(f"  Meta3: {d['meta3']}")
        print(f"  Realizado: {d['realizado']}")
        print(f"  %: {d['percent']}")
