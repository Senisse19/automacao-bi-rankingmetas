"""
Serviço de Dados Power BI.
Responsável por buscar dados reais de metas e receitas do Power BI via DAX,
integrando diretamente com o modelo semântico mapeado.
"""
import json
from datetime import datetime, timedelta
from clients.powerbi_client import PowerBIClient
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


from services.dax_queries import (
    get_realizado_query,
    get_metas_com_op_query,
    get_percentuais_gs_query,
    get_percentuais_com_op_query,
    get_receitas_query,
    get_metas_dept_query,
    get_percentuais_dept_query
)

class PowerBIDataFetcher:
    """
    Classe responsável por buscar dados de metas do Power BI via consultas DAX.
    Gerencia autenticação e orquestra as chamadas para diferentes tabelas e medidas.
    """
    
    def __init__(self):
        self.client = PowerBIClient()
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
                    }
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
                    }
                }
        except Exception as e:
            logger.error(f"Erro ao buscar percentuais Comercial/Operacional: {e}")
        
        return {"Comercial": {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0}, 
                "Operacional": {"pct_meta1": 0, "pct_meta2": 0, "pct_meta3": 0}}
    
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
        
        return {"outras": 0, "intercompany": 0, "nao_identificadas": 0, "sem_categoria": 0}
    
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
        
        # 3. Buscar metas GS (total)
        metas_gs = self.fetch_metas_departamento("GS_Metas", "GS")
        
        # 4. Buscar percentuais GS
        pct_gs = self.fetch_percentuais_gs()
        
        # 5. Buscar metas Comercial/Operacional
        metas_com_op = self.fetch_metas_comercial_operacional()
        
        # 6. Buscar percentuais Comercial/Operacional
        pct_com_op = self.fetch_percentuais_comercial_operacional()
        
        # 7. Configuração dos outros departamentos
        departamentos_config = [
            ("Corporate", "Corporate_Metas", "CORPORATE"),
            ("Educação", "Educação_Metas", "EDUCACAO"),
            ("Expansão", "Expansão_Metas", "EXPANSAO"),
            ("Franchising", "Franchising_Metas", "FRANCHISING"),
            ("Tax", "TAX_Metas", "TAX"),
            ("Tecnologia", "PJ360_Metas", "PJ"),
        ]
        
        # Montar dados formatados para GS
        total_gs = {
            "meta1": format_currency(metas_gs.get("meta1", 0)),
            "meta2": format_currency(metas_gs.get("meta2", 0)),
            "meta3": format_currency(metas_gs.get("meta3", 0)),
            "pct_meta1": pct_gs.get("pct_meta1", 0),
            "pct_meta2": pct_gs.get("pct_meta2", 0),
            "pct_meta3": pct_gs.get("pct_meta3", 0),
            "realizado": format_currency(realizados.get("Comercial", 0) + realizados.get("Operacional", 0)),
            "percent": format_percent(
                ((realizados.get("Comercial", 0) + realizados.get("Operacional", 0)) / metas_gs.get("meta1", 1)) * 100 
                if metas_gs.get("meta1", 0) > 0 else 0
            )
        }
        
        departamentos = []
        
        # Comercial
        com_metas = metas_com_op.get("Comercial", {})
        com_pct = pct_com_op.get("Comercial", {})
        com_real = realizados.get("Comercial", 0)
        departamentos.append({
            "nome": "Comercial",
            "meta1": format_currency(com_metas.get("meta1", 0)),
            "meta2": format_currency(com_metas.get("meta2", 0)),
            "meta3": format_currency(com_metas.get("meta3", 0)),
            "pct_meta1": com_pct.get("pct_meta1", 0),
            "pct_meta2": com_pct.get("pct_meta2", 0),
            "pct_meta3": com_pct.get("pct_meta3", 0),
            "realizado": format_currency(com_real),
            "percent": format_percent(
                (com_real / com_metas.get("meta1", 1)) * 100 
                if com_metas.get("meta1", 0) > 0 else 0
            )
        })
        
        # Operacional
        op_metas = metas_com_op.get("Operacional", {})
        op_pct = pct_com_op.get("Operacional", {})
        op_real = realizados.get("Operacional", 0)
        departamentos.append({
            "nome": "Operacional",
            "meta1": format_currency(op_metas.get("meta1", 0)),
            "meta2": format_currency(op_metas.get("meta2", 0)),
            "meta3": format_currency(op_metas.get("meta3", 0)),
            "pct_meta1": op_pct.get("pct_meta1", 0),
            "pct_meta2": op_pct.get("pct_meta2", 0),
            "pct_meta3": op_pct.get("pct_meta3", 0),
            "realizado": format_currency(op_real),
            "percent": format_percent(
                (op_real / op_metas.get("meta1", 1)) * 100 
                if op_metas.get("meta1", 0) > 0 else 0
            )
        })
        
        # Outros departamentos
        for nome, tabela, prefixo in departamentos_config:
            metas = self.fetch_metas_departamento(tabela, prefixo)
            pct = self.fetch_percentuais_departamento(prefixo)
            
            # Mapeamento de nome para chave de realizado (Tecnologia -> PJ)
            key_realizado = "PJ" if nome == "Tecnologia" else nome
            real = realizados.get(key_realizado, 0)
            
            departamentos.append({
                "nome": nome,
                "meta1": format_currency(metas.get("meta1", 0)),
                "meta2": format_currency(metas.get("meta2", 0)),
                "meta3": format_currency(metas.get("meta3", 0)),
                "pct_meta1": pct.get("pct_meta1", 0),
                "pct_meta2": pct.get("pct_meta2", 0),
                "pct_meta3": pct.get("pct_meta3", 0),
                "realizado": format_currency(real),
                "percent": format_percent(
                    (real / metas.get("meta1", 1)) * 100 
                    if metas.get("meta1", 0) > 0 else 0
                )
            })
        
        # Formatar receitas
        receitas = {
            "outras": format_currency(receitas_raw.get("outras", 0)),
            "intercompany": format_currency(receitas_raw.get("intercompany", 0)),
            "nao_identificadas": format_currency(receitas_raw.get("nao_identificadas", 0)),
            "sem_categoria": format_currency(receitas_raw.get("sem_categoria", 0))
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
