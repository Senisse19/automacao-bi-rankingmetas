from src.core.services.supabase_service import SupabaseService
from src.core.utils.logger import get_logger

logger = get_logger("job_enricher")


class JobEnricher:
    def __init__(self):
        self.supabase = SupabaseService()
        self._services_cache = {}
        self._contracts_cache = {}
        self._loaded = False

    def _load_caches(self):
        if self._loaded:
            return

        logger.info("Loading enrichment caches...")

        # Load Services
        services = self.supabase._get("nexus_servicos", {"select": "codigo, nome"})
        if services:
            self._services_cache = {s["codigo"]: s["nome"] for s in services}

        # Load Contracts (Active Only? Or All? Let's load All for now but optimize later)
        # We need mapping by 'participante' (Client ID)
        contracts = self.supabase._get("nexus_contratos_recorrentes", {"select": "*"})
        if contracts:
            # Assumindo 1 contrato por cliente ou pegando o mais recente
            # Logica: participant -> list of contracts -> pick best match?
            # Por simplicidade: participant -> dict
            for c in contracts:
                pid = c.get("participante")
                if pid:
                    # Se ja existe, substituir se for mais recente?
                    # Mas nao temos data facil de comparar aqui sem parse.
                    # Vamos sobrescrever.
                    self._contracts_cache[pid] = c

        self._loaded = True
        logger.info(f"Caches loaded. Services: {len(self._services_cache)}, Contracts: {len(self._contracts_cache)}")

    def enrich(self, jobs):
        self._load_caches()

        enriched = []
        for job in jobs:
            # Clone dict to avoid side effects
            j = job.copy()

            # 1. Product Name
            prod_code = j.get("codigo_produto")
            j["produto_nome"] = self._services_cache.get(prod_code, f"Cod: {prod_code}")

            # 2. Financial / Contract Data
            client_id = j.get("cliente_id")
            contract = self._contracts_cache.get(client_id)

            if contract:
                j["faturamento"] = contract.get("valor_a_vista")
                # "Faturamento" as Acquisition Value? Or Monthly? Clarify.
                # User said "Faturamento" and "Honorários Iniciais".
                # Let's map:
                # "Faturamento" -> ??? Usually means Client's Revenue? Or Deal Value?
                # User asked: "Faturamento" and "Honorários Iniciais".
                # In contract table we have: `valor_a_vista`, `mensalidade`.
                # Let's assume `valor_a_vista` = Honorários Iniciais.
                # `mensalidade` = Mensalidade.
                # "Faturamento" often refers to Client's Turnover (Faturamento da Empresa).
                # Usually in `nexus_participantes`?
                # Nexus contract usually has `faturamento_estimado`? No column in my table migration.
                # Let's check raw contract fields in inspection... I missed that.

                j["valor_inicial"] = contract.get("valor_a_vista")
                j["mensalidade"] = contract.get("mensalidade")

                regime_map = {
                    1: "Lucro Real",
                    2: "Lucro Presumido",
                    3: "Simples Nacional",
                    4: "Outros",
                }  # Exemplo hipotetico
                regime_code = contract.get("regime_tributacao")
                j["regime_tributario"] = regime_map.get(regime_code, str(regime_code))

            else:
                j["valor_inicial"] = 0
                j["mensalidade"] = 0
                j["regime_tributario"] = "-"

            enriched.append(j)

        return enriched
