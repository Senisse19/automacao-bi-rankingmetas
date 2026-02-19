from modules.unidades.runner import UnidadesAutomation
from modules.metas.runner import MetasAutomation
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("jobs")

# --- Job Wrappers ---


def job_unidades_daily(recipients=None, template_content=None):
    """Executa a automação de Unidades: Relatório Diário."""
    logger.info("Iniciando Unidades Daily (Dynamic)")
    SupabaseService().log_event("job_start", {"job": "unidades_daily"})
    ua = UnidadesAutomation()
    # Pass recipients if provided
    ua.process_reports(
        daily=True,
        weekly=False,
        recipients=recipients,
        template_content=template_content,
    )


def job_unidades_weekly(recipients=None, template_content=None):
    """Executa a automação de Unidades: Relatório Semanal."""
    logger.info("Iniciando Unidades Weekly (Dynamic)")
    SupabaseService().log_event("job_start", {"job": "unidades_weekly"})
    ua = UnidadesAutomation()
    ua.process_reports(
        daily=False,
        weekly=True,
        recipients=recipients,
        template_content=template_content,
    )


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
    from modules.ina.runner import InaAutomation

    logger.info("Iniciando Painel INA Automation")
    SupabaseService().log_event("job_start", {"job": "painel_ina"})

    ina = InaAutomation()
    ina.run(recipients=recipients, template_content=template_content)


def job_jobs_diario(recipients=None, template_content=None):
    """Executa a automação de Jobs: Relatório Diário (Tax/Corp/Diretoria)."""
    from modules.jobs.automation import JobsAutomation

    logger.info("Iniciando Jobs Diario")
    SupabaseService().log_event("job_start", {"job": "jobs_diario"})

    ja = JobsAutomation()
    ja.process_reports(daily=True, recipients=recipients, template_content=template_content)


def job_jobs_semanal(recipients=None, template_content=None):
    """Executa a automação de Jobs: Relatório Semanal."""
    from modules.jobs.automation import JobsAutomation

    logger.info("Iniciando Jobs Semanal")
    SupabaseService().log_event("job_start", {"job": "jobs_semanal"})

    ja = JobsAutomation()
    ja.process_reports(
        daily=False,
        weekly=True,
        recipients=recipients,
        template_content=template_content,
    )


# --- Mapping ---

JOB_MAPPING = {
    "metas_diarias": job_metas,
    "unidades": job_unidades_daily,  # Default 'unidades' key to Daily
    "unidades_diario": job_unidades_daily,
    "unidades_semanal": job_unidades_weekly,
    "ranking_geral": job_ranking_geral,
    "painel_ina": job_painel_ina,
    "jobs_diario": job_jobs_diario,
    "jobs_semanal": job_jobs_semanal,
    # Master Sync
    "sync_master_daily": lambda recipients=None, template_content=None: __import__(
        "modules.sync.master_runner", fromlist=["run"]
    ).run(),
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
        SupabaseService().log_event("job_error", {"job": job_func.__name__, "error": str(e)}, level="error")
        # alert_admin(error_msg) # TODO: Decouple admin alert
