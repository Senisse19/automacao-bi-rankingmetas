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
        
        # Configure Autoscaling Retry
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        svc = SupabaseService()
        self.model_map = svc.get_setting("nexus_model_map", {})
        self.type_map = svc.get_setting("unidades_type_map", {})

    def _get_paginated_latest(self, endpoint: str, min_date: str | None = None) -> list:
        """
        Busca os dados mais recentes da API.
        Nota: A ordenação da API parece ser ASC ou mista (mais antigos primeiro?),
        então precisamos escanear TODAS as páginas para encontrar os dados mais novos (ex: 2026).
        O filtro de `min_date` é aplicado somente nos RESULTADOS finais, não interrompe a busca.
        """
        url = f"{self.api_url}/{endpoint}/"
        try:
            # 1. Fetch first page to determine type
            logger.info(f"Fetching {endpoint} page 1...")
            resp = self.session.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, list):
                all_items = data
                page = 2
                
                # We cannot rely on dates to stop early because Page 1 has 2015/2012 
                # but we need 2026 which might be on Page 50+.
                # Restoring full scan loop.

                while len(data) >= 10: 
                    if len(all_items) > 100000: # Original safety limit
                        logger.warning("Max items limit reached (100k), stopping.")
                        break
                        
                    if page % 5 == 0:
                        logger.info(f"Fetching {endpoint} page {page}...")
                        
                    try:
                        p_resp = self.session.get(f"{url}?page={page}", headers=self.headers, timeout=10)
                        if p_resp.status_code == 404:
                            break
                        p_data = p_resp.json()
                        if not p_data or not isinstance(p_data, list):
                            break
                        data = p_data
                        
                        all_items.extend(data)
                        page += 1
                    except Exception as e:
                        logger.error(f"Stop fetching: {e}")
                        break
                
                # Filter results by date if min_date provided
                if min_date:
                    logger.info(f"Filtering {len(all_items)} items for min_date {min_date}...")
                    filtered = []
                    for x in all_items:
                        d_contrato = x.get("data")
                        d_cancel = x.get("data_cancelamento")
                        
                        # Keep if Contract is recent OR Cancellation is recent
                        if (d_contrato and d_contrato >= min_date) or \
                           (d_cancel and d_cancel >= min_date):
                            filtered.append(x)
                            
                    logger.info(f"Found {len(filtered)} items.")
                    return filtered
                    
                return all_items
                
            elif isinstance(data, dict):
                # Standard pagination logic
                count = data.get("count", 0)
                results = data.get("results", [])
                
                if count == 0:
                    return results
                    
                page_size = len(results) if results else 100
                if page_size == 0: page_size = 100
                    
                total_pages = math.ceil(count / page_size)
                logger.info(f"Total: {count}, Pages: {total_pages}")
                
                all_items = []
                start_page = max(1, total_pages - pages_to_fetch + 1)
                
                for p in range(start_page, total_pages + 1):
                    # We already have page 1 if start_page==1, but let's just refetch for simplicity logic
                    # or optimize.
                    if p == 1 and start_page == 1:
                        all_items.extend(results)
                        continue
                        
                    logger.info(f"Fetching page {p}...")
                    p_resp = self.session.get(f"{url}?page={p}", headers=self.headers)
                    if p_resp.status_code == 200:
                        all_items.extend(p_resp.json().get("results", []))
                
                return all_items
            
            return []
            
        except Exception as e:
            logger.error(f"Error in _get_paginated_latest: {e}")
            return []

    def _get_all_participantes(self) -> dict:
        """Busca todos os participantes (consultores/gerentes) para lookup."""
        logger.debug("Skipping participantes fetch.")
        return {}

    def _get_all_unidades(self) -> dict:
        """Busca TODAS as unidades para lookup (cache local)."""
        logger.info("Fetching lookups: Unidades...")
        results = self._get_paginated_latest("unidades")
        # Map ID -> {nome, cidade, uf}
        unidades_map = {}
        for u in results:
            unidades_map[u.get("codigo")] = {
                "nome": u.get("nome", f"Unidade {u.get('codigo')}"),
                "cidade": u.get("cidade", ""),
                "uf": u.get("uf", "")
            }
        return unidades_map

    def fetch_data_for_range(self, start_date: str, end_date: str) -> dict:
        """
        Busca 'modelos' e 'unidades', vincula as informações e filtra por data (inclusivo).
        
        Args:
            start_date: string "YYYY-MM-DD"
            end_date: string "YYYY-MM-DD"
        """
        # 1. Fetch Lookups (Dimension Tables)
        participantes_map = self._get_all_participantes()
        unidades_map = self._get_all_unidades()
        
        # 2. Fetch Facts (Modelos) filtered by min_date
        # Note: We filter by min_date to avoid fetching 10 years of sales
        modelos = self._get_paginated_latest("modelos", min_date=start_date)
        
        new_units = []
        cancelled_units = []
        upsell_units = []
        
        # Parse dates for comparison
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        for m in modelos:
            # Check dates
            # Check dates - prefer data_contrato as per user mapping, fallback to data
            data_contrato_str = m.get("data_contrato") or m.get("data")
            data_cancelamento_str = m.get("data_cancelamento")
            
            # LINK: Unidade Data (from Unidades lookup)
            uid = m.get("unidade")
            unit_data = unidades_map.get(uid, {"nome": f"Unidade {uid}", "cidade": "-", "uf": "-"})
            unit_name = unit_data["nome"]
            unit_cidade = unit_data["cidade"]
            unit_uf = unit_data["uf"]
            
            # LINK: Consultant Name (from Participantes lookup)
            consultor_id = m.get("consultor_venda")
            consultor_nome = participantes_map.get(consultor_id, "N/A")

            # LINK: Manager Name (from Participantes lookup)
            gerente_id = m.get("gerente_venda")
            gerente_nome = participantes_map.get(gerente_id, "N/A")
            
            # Resolve Model Name and Type
            model_id = m.get("modelo")
            model_name = self.model_map.get(model_id, f"Modelo {model_id}")
            
            # Resolve Type (Franquia/Licença)
            type_id = m.get("tipo_franquia") or m.get("tipo_contrato")
            type_name = self.type_map.get(str(type_id), f"Tipo {type_id}")
            
            # Additional Fields requested
            # (taxa de aquisição, valor de crm -> rede, percentual de retenção, periodo de contrato)
            valor_aquisicao = m.get("valor", 0)
            
            # Rede de distribuição (Solicitado: Tipo Franquia ID - Nome)
            rede_distribuicao = f"{type_id} - {type_name}" if type_id else "-"
            
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
                "anos_contrato": anos_contrato,
                "data": data_contrato_str
            }
            
            # Logic: New Unit (Check if data_contrato is in range)
            if data_contrato_str:
                try:
                    dt = datetime.strptime(data_contrato_str, "%Y-%m-%d")
                    if start_dt <= dt <= end_dt:
                        new_units.append(item)
                except:
                    pass
                 
            # Logic: Cancelled
            if m.get("cancelamento") == 1 and data_cancelamento_str:
                try:
                    dt = datetime.strptime(data_cancelamento_str, "%Y-%m-%d")
                    if start_dt <= dt <= end_dt:
                        cancelled_units.append(item)
                except:
                    pass
            
            # Upsell Logic (Placeholder)
            
        return {
            "date": end_date,
            "start_date": start_date,
            "new": new_units,
            "cancelled": cancelled_units,
            "upsell": upsell_units
        }

    def fetch_unit_name(self, uid: int | str) -> str:
        """Fallback to fetch single unit name"""
        try:
            url = f"{self.api_url}/unidades/{uid}/"
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                return resp.json().get("nome")
        except:
            pass
        return f"Unidade {uid}"
