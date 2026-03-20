import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from src.core.jobs import PBI_DATASETS, job_refresh_dashboards, job_refresh_pbi_token
from src.core.services.supabase_service import SupabaseService

logger = logging.getLogger("api_pbi")
router = APIRouter()


@router.post("/refresh-token")
async def refresh_pbi_token(background_tasks: BackgroundTasks):
    """
    Dispara a atualização do token do Power BI em background.
    """
    logger.info("[PBI] Recebida solicitação de refresh de token Power BI")
    background_tasks.add_task(job_refresh_pbi_token)
    return {"status": "accepted", "message": "Processo de atualização de token iniciado em background."}


@router.get("/token")
async def get_pbi_token():
    """
    Retorna o token atual do Power BI armazenado no Supabase.
    """
    try:
        supabase = SupabaseService()
        pbi_data = supabase.get_setting("pbi_access_token")

        if not pbi_data:
            raise HTTPException(status_code=404, detail="Token não encontrado ou ainda não gerado.")

        return pbi_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PBI] Erro ao buscar token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar token: {str(e)}")


class RefreshDashboardsRequest(BaseModel):
    """Requisição para refresh de dashboards. Use 'all' para atualizar todos."""
    dashboards: list[str]


@router.post("/refresh-dashboards")
async def refresh_dashboards(
    request: RefreshDashboardsRequest,
    background_tasks: BackgroundTasks,
):
    """
    Dispara o refresh de um ou mais datasets do Power BI.

    Corpo: {"dashboards": ["Geral (Metas)", "Painel de Unidades"]}
    Para atualizar tudo: {"dashboards": ["all"]}
    """
    # Valida os nomes fornecidos (exceto "all" que é especial)
    nomes_validos = set(PBI_DATASETS.keys())
    invalidos = [d for d in request.dashboards if d != "all" and d not in nomes_validos]
    if invalidos:
        raise HTTPException(
            status_code=422,
            detail=f"Dashboards desconhecidos: {invalidos}. Válidos: {sorted(nomes_validos)}",
        )

    logger.info(f"[PBI] Solicitação de refresh recebida: {request.dashboards}")
    background_tasks.add_task(job_refresh_dashboards, request.dashboards)
    return {"status": "accepted", "dashboards": request.dashboards}


@router.get("/dashboards")
async def list_dashboards():
    """
    Retorna a lista de dashboards disponíveis para refresh.
    O Admin Panel usa este endpoint para preencher os checkboxes.
    """
    return {
        "dashboards": sorted(PBI_DATASETS.keys()),
        "total": len(PBI_DATASETS),
    }
