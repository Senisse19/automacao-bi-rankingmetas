import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import math
from datetime import datetime, timedelta
from config import UNIDADES_CONFIG
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("unidades_client")

class UnidadesClient:
    """
    Cliente para interação com a API do Nexus (Unidades).
    Gerencia autenticação, paginação robusta e filtragem de dados.
    """
    def __init__(self):
        self.api_url = UNIDADES_CONFIG["api_url"]
        self.token = UNIDADES_CONFIG["token"]
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.token
        }
        
        # Configurar Repetição com Escalonamento Automático
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        svc = SupabaseService()
        self.model_map = svc.get_setting("nexus_model_map", {})
        self.type_map = svc.get_setting("unidades_type_map", {})

    def fetch_all_from_source(self, endpoint: str) -> list:
        """
        Busca TODOS os dados da API Nexus (Source) paginando via 'page'.
        Ignora o mirror Supabase.
        """
        all_items = []
        page = 1
        limit = 500  # Safe batch size
        
        url = f"{self.api_url}/{endpoint}/"
        logger.info(f"Fetching full data from SOURCE API: {url}")
        
        while True:
            try:
                params = {"page": page, "limit": limit}
                
                # Direct Request using Session
                resp = self.session.get(url, headers=self.headers, params=params, timeout=30)
                
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch page {page}: {resp.status_code} - {resp.text[:100]}")
                    break
                    
                data = resp.json()
                
                # Handle potential wrappers
                if isinstance(data, dict):
                    if 'data' in data: items = data['data']
                    elif 'results' in data: items = data['results']
                    else: items = [] # Unknown format or empty dict
                elif isinstance(data, list):
                    items = data
                else:
                    logger.error(f"Unknown response format: {type(data)}")
                    break
                    
                if not items:
                    break
                    
                all_items.extend(items)
                logger.info(f"Page {page} fetched {len(items)} items. Total so far: {len(all_items)}")
                
                if len(items) < limit:
                    # Last page
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"Exception on page {page}: {e}")
                break
                
        return all_items

    def _get_paginated_latest(self, endpoint: str, min_date: str | None = None) -> list:
        """
        Busca dados do Supabase (Mirror) em vez da API Externa.
        Mapeia 'endpoint' para tabelas 'nexus_*'.
        """
        svc = SupabaseService()
        table_map = {
            "unidades": "nexus_unidades",
            "modelos": "nexus_modelos",
            "participantes": "nexus_participantes"
        }
        table = table_map.get(endpoint)
        if not table:
            logger.error(f"Endpoint/Tabela desconhecido: {endpoint}")
            return []
            
        try:
            logger.info(f"Fetching data from Supabase table: {table}")
            
            # Construir Consulta
            # Queremos TODOS os dados efetivamente, ou filtrar por data se a coluna existir
            params = {
                "select": "*"
            }
            
            # Otimização: Se buscar 'modelos' com min_date, aplicar filtro diretamente
            if endpoint == "modelos" and min_date:
                # Filtrar por data_contrato OU data (legado)
                # Supabase REST não suporta OR complexo facilmente em um parâmetro sem string raw
                # Então buscamos um pouco mais e filtramos em Python, ou usamos 'gte'
                # Vamos simplesmente buscar tudo por enquanto ou ordenar por data decrescente com limite de 1000? 
                # Idealmente sincronizamos TODO o histórico, então devemos buscar tudo.
                # No entanto, sincronizar 500k linhas via REST pode ser lento.
                # Mas 'nexus_modelos' tem apenas ~600 linhas no teste?
                pass
                
            # Buscar TODAS as linhas (auxiliar de paginação)
            all_items = []
            offset = 0
            limit = 1000
            
            while True:
                p = params.copy()
                p["offset"] = offset
                p["limit"] = limit
                # Ordenar por id para garantir consistência
                p["order"] = "id.asc"
                
                chunk = svc._get(table, p)
                if not chunk:
                    break
                    
                all_items.extend(chunk)
                if len(chunk) < limit:
                    break
                    
                offset += limit
                
            logger.info(f"Fetched {len(all_items)} rows from {table}.")
            
            # Pós-filtrar por min_date se solicitado (para 'modelos')
            if min_date and endpoint == "modelos":
                 filtered = []
                 for x in all_items:
                    d_contrato = x.get("data_contrato") or x.get("data")
                    d_cancel = x.get("data_cancelamento")
                    
                    if (d_contrato and d_contrato >= min_date) or \
                       (d_cancel and d_cancel >= min_date):
                        filtered.append(x)
                 return filtered
                 
            return all_items

        except Exception as e:
            logger.error(f"Error fetching from Supabase ({endpoint}): {e}")
            return []

    def _get_all_participantes(self) -> dict:
        """Busca todos os participantes (consultores/gerentes) para lookup via Supabase."""
        logger.info("Fetching lookups: Participantes...")
        results = self._get_paginated_latest("participantes")
        # Mapear ID -> Nome (Assumir campo 'nome' ou 'NOME')
        pmap = {}
        for p in results:
            uid = p.get("id") or p.get("codigo")
            pmap[uid] = p.get("nome") or p.get("NOME") or f"Partic. {uid}"
        return pmap

    def _get_all_unidades(self) -> dict:
        """Busca TODAS as unidades para lookup (cache local)."""
        logger.info("Fetching lookups: Unidades...")
        results = self._get_paginated_latest("unidades")
        # Mapear ID -> {nome, cidade, uf, raw_data}
        unidades_map = {}
        for u in results:
            uid = u.get("codigo") or u.get("id")
            unidades_map[uid] = {
                "nome": u.get("nome", f"Unidade {uid}"),
                "cidade": u.get("cidade", ""),
                "uf": u.get("uf", ""),
                "raw_data": u.get("raw_data") or {}
            }
        return unidades_map

    def fetch_data_for_range(self, start_date: str, end_date: str) -> dict:
        """
        Busca 'modelos' e 'unidades', vincula as informações e filtra por data (inclusivo).
        
        Args:
            start_date: string "YYYY-MM-DD"
            end_date: string "YYYY-MM-DD"
        """
        # 1. Buscar Lookups (Tabelas de Dimensão)
        participantes_map = self._get_all_participantes()
        unidades_map = self._get_all_unidades()
        
        # 2. Buscar Fatos (Modelos) filtrados por min_date
        # Nota: Filtramos por min_date para evitar buscar 10 anos de vendas
        modelos = self._get_paginated_latest("modelos", min_date=start_date)
        
        new_units = []
        cancelled_units = []
        upsell_units = []
        
        # Parsear datas para comparação
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        for m in modelos:
            # Verificar datas - preferir data (view Supabase) ou fallback
            data_contrato_str = m.get("data") or m.get("data_contrato")
            data_cancelamento_str = m.get("data_cancelamento")
            
            raw_data = m.get("raw_data") or {}
            
            # Correção Temporária: Hardcode Modelo 40 ausente (Studio Store)
            if 40 not in self.model_map:
                self.model_map[40] = "Studio Store"
            if "40" not in self.model_map:
                self.model_map["40"] = "Studio Store"
            
            # LINK: Dados da Unidade (do lookup de Unidades)
            uid = m.get("unidade")
            unit_data = unidades_map.get(uid)
            
            # Fallback: Se unidade não estiver no cache, buscar nome na API Nexus
            if not unit_data:
                logger.info(f"Unit {uid} not in cache, fetching from API...")
                fetched_name = self.fetch_unit_name(uid)
                unit_data = {"nome": fetched_name, "cidade": "-", "uf": "-", "raw_data": {}}
                # Armazenar em cache para buscas futuras nesta sessão
                unidades_map[uid] = unit_data
            
            # Usar nome de nexus_unidades diretamente
            base_unit_name = unit_data["nome"]
            # Formato: "Unidade {ID} - {Nome}" se o nome ainda não estiver formatado
            if base_unit_name and "Unidade" not in str(base_unit_name):
                unit_name = f"Unidade {uid} - {base_unit_name}"
            else:
                unit_name = base_unit_name or f"Unidade {uid}"

            unit_cidade = unit_data["cidade"]
            unit_uf = unit_data["uf"]
            
            # LINK: Nome do Consultor (do lookup de Participantes)
            consultor_id = m.get("consultor_venda")
            consultor_nome = participantes_map.get(consultor_id, "N/A")

            # LINK: Nome do Gerente (do lookup de Participantes)
            gerente_id = m.get("gerente_venda")
            gerente_nome = participantes_map.get(gerente_id, "N/A")
            
            # Resolver Nome do Modelo e Tipo (Preferir raw_data do Data Lake)
            model_name = raw_data.get("modelo_nome")
            if not model_name:
                model_id = m.get("modelo")
                model_name = self.model_map.get(str(model_id), f"Modelo {model_id}")
            
            # Resolver Tipo (Rede Distribuição)
            type_name = raw_data.get("tipo_nome")
            if not type_name:
                type_id = m.get("tipo_franquia") or m.get("tipo_contrato")
                type_name = self.type_map.get(str(type_id), f"Tipo {type_id}")
            
            # Campos Adicionais solicitados
            valor_aquisicao = m.get("valor", 0)
            
            rede_distribuicao = type_name # Usar nome completo do tipo como Rede
            
            percentual_retencao = m.get("percentual_retencao", 0)
            anos_contrato = m.get("anos", 0)

            item = {
                "codigo": uid,
                "nome": unit_name,
                "cidade": unit_cidade,
                "uf": unit_uf,
                "modelo": model_name,
                "tipo": type_name,
                "consultor": consultor_nome,
                "gerente": gerente_nome,
                "valor": valor_aquisicao,
                "rede_distribuicao": rede_distribuicao,
                "percentual_retencao": percentual_retencao,
                "royalties": m.get("royalties", 0),
                "crm": m.get("crm", 0),
                "anos_contrato": anos_contrato,
                "data": data_contrato_str,
                "raw_data": raw_data,
                "unit_raw_data": unit_data.get("raw_data", {})
            }
            
            # Lógica: Nova Unidade (Verificar se data_contrato está no intervalo)
            # Filtrar status ativo
            status = m.get("status")
            
            if data_contrato_str:
                try:
                    clean_date = data_contrato_str[:10]
                    dt = datetime.strptime(clean_date, "%Y-%m-%d")
                    
                    if start_dt <= dt <= end_dt:
                        # Lógica de page.tsx:
                        # newUnits = items.filter(i => i.status === "Ativo")
                        # upsellUnits = ... raw_data.tipo_venda === 'Upsell' or is_upsell
                        
                        is_upsell = raw_data.get("tipo_venda") == "Upsell" or raw_data.get("is_upsell") is True
                        
                        if is_upsell:
                            upsell_units.append(item)
                        elif status == "Ativo": 
                            new_units.append(item)
                        else:
                            # Pode estar Cancelada no mesmo período? Tratado abaixo.
                            pass
                            
                except Exception as e:
                    pass
                 
            # Lógica: Cancelada
            # page.tsx: i.status === "Cancelado" || i.raw_data?.cancelamento === 1
            is_cancelled = status == "Cancelado" or raw_data.get("cancelamento") == 1
            
            if is_cancelled and data_cancelamento_str:
                try:
                    clean_cancel = data_cancelamento_str[:10]
                    dt = datetime.strptime(clean_cancel, "%Y-%m-%d")
                    if start_dt <= dt <= end_dt:
                        cancelled_units.append(item)
                except Exception as e:
                     pass
            
            # Fallback para flag de cancelamento no data lake sem data?
            # Geralmente precisamos da data para saber SE foi cancelada HOJE.
            # Assumindo que data_cancelamento corresponde.
                        
        return {
            "date": end_date,
            "start_date": start_date,
            "new": new_units,
            "cancelled": cancelled_units,
            "upsell": upsell_units
        }

    def fetch_unit_name(self, uid: int | str) -> str:
        """Fallback para buscar nome de unidade única"""
        try:
            url = f"{self.api_url}/unidades/{uid}/"
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("nome")
        except:
            pass
        return f"Unidade {uid}"
