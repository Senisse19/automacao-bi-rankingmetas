from src.core.services.supabase_service import SupabaseService
from src.core.utils.logger import get_logger
from src.modules.metas.runner import MetasAutomation

logger = get_logger("jobs")

# --- Job Wrappers ---


def job_metas(recipients=None, template_content=None):
    """Executa a automação de Metas (Power BI)."""
    logger.info("Iniciando Metas Automation (Dynamic)")
    SupabaseService().log_event("job_start", {"job": "metas"})
    ma = MetasAutomation()
    ma.run(recipients=recipients, template_content=template_content)


def job_ranking_geral(recipients=None, template_content=None):
    """Placeholder para Ranking Geral se for diferente de Metas."""
    logger.info("Iniciando Ranking Geral (Placeholder)")
    SupabaseService().log_event("job_start", {"job": "ranking_geral"})
    # Se for o mesmo que metas, apenas chame metas
    job_metas(recipients, template_content=template_content)


def job_painel_ina(recipients=None, template_content=None):
    """Executa a automação do Painel INA."""
    from src.modules.ina.runner import InaAutomation

    logger.info("Iniciando Painel INA Automation")
    SupabaseService().log_event("job_start", {"job": "painel_ina"})

    ina = InaAutomation()
    ina.run(recipients=recipients, template_content=template_content)


def job_unidades(recipients=None, template_content=None, report_type="daily"):
    """Executa a automação de Unidades (Power BI)."""
    from src.modules.unidades.runner import UnidadesAutomation

    logger.info(f"Iniciando Unidades Automation ({report_type})")
    SupabaseService().log_event("job_start", {"job": f"unidades_{report_type}"})

    ua = UnidadesAutomation()
    ua.run(report_type=report_type, recipients=recipients, template_content=template_content)


def job_refresh_pbi_token():
    """Tarefa de background para renovar o token do Power BI."""
    from datetime import datetime

    from src.core.clients.powerbi_client import PowerBIClient
    from src.core.services.supabase_service import SupabaseService

    supabase = SupabaseService()
    logger.info("[JOB] Iniciando Refresh do Token Power BI...")
    supabase.log_event("job_start", {"job": "pbi_token_refresh"})

    try:
        pbi = PowerBIClient()
        if pbi.authenticate():
            token = pbi.token
            expires_at = pbi.token_expiry

            pbi_token_data = {
                "token": token,
                "expires_at": expires_at,
                "updated_at": datetime.now().isoformat()
            }

            # Persistir no Supabase
            success = supabase.update_setting("pbi_access_token", pbi_token_data)

            if success:
                logger.info("[JOB] Token Power BI renovado e persistido com sucesso.")
                supabase.log_event("job_success", {"job": "pbi_token_refresh"})
                return True
            else:
                logger.error("[JOB] Falha ao persistir o token no Supabase.")
                supabase.log_event(
                    "job_error",
                    {"job": "pbi_token_refresh", "error": "Falha na persistencia no Supabase"},
                )
                return False
        else:
            logger.error("[JOB] Falha na autenticação Azure AD.")
            supabase.log_event(
                "job_error",
                {"job": "pbi_token_refresh", "error": "Falha na autenticacao Microsoft"},
            )
            return False
    except Exception as e:
        logger.error(f"[JOB] Erro critico no refresh do token PBI: {e}")
        supabase.log_event("job_error", {"job": "pbi_token_refresh", "error": str(e)})
        return False


# --- Mapeamento de Datasets do Power BI ---

# Workspace compartilhado por todos os relatórios
PBI_WORKSPACE_ID = "4600324e-148c-4aae-a743-601628c04d29"

# Mapeamento de nome amigável → ID do dataset no Power BI
PBI_DATASETS: dict[str, str] = {
    "Composição de Receitas": "26873b5b-7e88-48b9-8a23-e504178fcf8a",
    "Geral (Metas)": "5f1e9f0f-8388-438d-a0be-6a5e13bb3ce4",
    "Painel de Unidades": "f476a231-a82f-405d-b0e5-1a4147e172ca",
    "Painel a Receber": "97104bd3-fa7f-4a40-94f8-4989254e7f48",
    "Painel de Inadimplência": "92174395-c9b1-4b2c-b491-137fff6bb634",
    "Painel de Recuperados": "36e4beb2-2684-4282-ace0-50d8ca7f6658",
}


def job_refresh_dashboards(dashboards: list[str]) -> dict:
    """
    Orquestra o fluxo completo de atualização de dashboards do Power BI:

    1. Gera e persiste o Bearer Token no Supabase.
    2. Dispara o refresh de cada dataset selecionado.
    3. Loga o resultado individual e o resumo final na tabela automation_logs.

    Aceita lista de nomes amigáveis ou ["all"] para atualizar tudo.
    """
    from datetime import datetime

    from src.core.clients.powerbi_client import PowerBIClient

    supabase = SupabaseService()
    results: dict[str, bool] = {}

    # "all" expande para todos os dashboards conhecidos
    targets = list(PBI_DATASETS.keys()) if "all" in dashboards else dashboards

    logger.info(f"[JOB] Iniciando refresh de {len(targets)} dashboard(s): {targets}")
    supabase.log_event("job_start", {"job": "pbi_refresh_dashboards", "dashboards": targets})

    try:
        pbi = PowerBIClient()

        # Etapa 1: Gera o token e persiste no Supabase antes de qualquer refresh
        logger.info("[JOB] Autenticando no Azure AD para refresh dos dashboards...")
        if not pbi.authenticate():
            logger.error("[JOB] Falha na autenticação Azure AD. Refresh cancelado.")
            supabase.log_event("job_error", {
                "job": "pbi_refresh_dashboards",
                "error": "Falha na autenticação Azure AD",
            })
            return {}

        # Persiste o token gerado para uso futuro (ex: GET /pbi/token)
        supabase.update_setting("pbi_access_token", {
            "token": pbi.token,
            "expires_at": pbi.token_expiry,
            "updated_at": datetime.now().isoformat(),
        })
        logger.info("[JOB] Token Bearer gerado e persistido no Supabase.")

        # Etapa 2: Dispara o refresh de cada dataset
        for name in targets:
            dataset_id = PBI_DATASETS.get(name)
            if not dataset_id:
                logger.warning(f"[JOB] Dashboard desconhecido ignorado: '{name}'")
                results[name] = False
                continue

            success = pbi.trigger_dataset_refresh(dataset_id, workspace_id=PBI_WORKSPACE_ID)
            results[name] = success
            log_level = "job_success" if success else "job_error"
            supabase.log_event(log_level, {"job": "pbi_refresh_dashboards", "dashboard": name})

        # Etapa 3: Log de conclusão global com resumo dos resultados
        failed = [n for n, ok in results.items() if not ok]
        if failed:
            logger.warning(f"[JOB] Refresh concluído com falhas: {failed}")
            supabase.log_event("job_error", {
                "job": "pbi_refresh_dashboards",
                "error": f"Falha em {len(failed)} dashboard(s)",
                "failed": failed,
                "results": results,
            })
        else:
            logger.info(f"[JOB] Refresh concluído com sucesso. Total: {len(targets)} dashboard(s).")
            supabase.log_event("job_success", {
                "job": "pbi_refresh_dashboards",
                "total": len(targets),
                "results": results,
            })

    except Exception as e:
        logger.error(f"[JOB] Erro crítico no refresh de dashboards: {e}")
        supabase.log_event("job_error", {
            "job": "pbi_refresh_dashboards",
            "error": str(e),
        })

    return results


# --- Mapping ---

JOB_MAPPING = {
    "metas_diarias": job_metas,
    "ranking_geral": job_ranking_geral,
    "painel_ina": job_painel_ina,
    "unidades_diarias": lambda **kwargs: job_unidades(report_type="daily", **kwargs),
    "unidades_semanais": lambda **kwargs: job_unidades(report_type="weekly", **kwargs),
    "pbi_token_refresh": job_refresh_pbi_token,
    "pbi_refresh_dashboards": job_refresh_dashboards,
}


def safe_run_job(job_func, recipients=None, template_content=None):
    """Wrapper para executar jobs com tratamento de erro e logs."""
    try:
        if recipients:
            job_func(recipients=recipients, template_content=template_content)
        else:
            job_func(template_content=template_content)
        SupabaseService().log_event("job_success", {"job": job_func.__name__})
    except Exception as e:
        error_msg = f"❌ Erro na execução de '{job_func.__name__}': {str(e)}"
        logger.error(error_msg)
        SupabaseService().log_event("job_error", {"job": job_func.__name__, "error": str(e)})
        # alert_admin(error_msg) # TODO: Decouple admin alert
