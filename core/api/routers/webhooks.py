"""
Router de Webhooks para sincronização de tabelas do Nexus com o Supabase.
Recebe eventos INSERT/UPDATE do sistema externo e dispara o sync em background.
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService

logger = logging.getLogger("api_webhooks")
router = APIRouter()

# Campos mapeados da API Nexus → coluna da tabela Supabase
CONTAS_FIELD_MAP = {
    "id": "id",
    "codigo": "codigo",
    "razao_social": "razao_social",
    "bandeira": "bandeira",
    "descricao": "descricao",
    "data_emissao": "data_emissao",
    "data_vencimento": "data_vencimento",
    "valor_contas_receber": "valor",
    "personalizar": "personalizar",
}

# Roteador: qual endpoint do Nexus corresponde a cada tabela do Supabase
TABLE_SOURCE_MAP = {
    "nexus_contas_receber": "contas-receber",
}

# Mapeamento de campo → coluna para cada tabela sincronizável
TABLE_FIELD_MAPS = {
    "nexus_contas_receber": CONTAS_FIELD_MAP,
}


def _sync_table(table: str) -> None:
    """Executa o sync completo de uma tabela Nexus → Supabase."""
    source_endpoint = TABLE_SOURCE_MAP.get(table)
    field_map = TABLE_FIELD_MAPS.get(table)

    if not source_endpoint or not field_map:
        logger.error(f"[WEBHOOK] Tabela '{table}' sem mapeamento configurado.")
        return

    try:
        client = UnidadesClient()
        svc = SupabaseService()

        logger.info(f"[WEBHOOK] Iniciando sync de '{table}' via '{source_endpoint}'...")
        data = client.fetch_all_from_source(source_endpoint)
        logger.info(f"[WEBHOOK] {len(data)} registros obtidos do Nexus.")

        if not data:
            logger.warning(f"[WEBHOOK] Nenhum dado retornado para '{table}'. Sync encerrado.")
            return

        # Mapeia os campos para o schema da tabela Supabase
        agora = datetime.now().isoformat()
        batch = []
        for item in data:
            row = {col_dest: item.get(col_src) for col_src, col_dest in field_map.items()}
            row["updated_at"] = agora
            batch.append(row)

        # Upsert em lotes de 500
        chunk_size = 500
        total_chunks = (len(batch) + chunk_size - 1) // chunk_size

        for i in range(0, len(batch), chunk_size):
            chunk = batch[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            conflict_col = "codigo" if table == "nexus_contas_receber" else "id"
            success = svc.upsert_data(table, chunk, on_conflict=conflict_col)

            if success:
                logger.info(f"[WEBHOOK] Chunk {chunk_num}/{total_chunks} upsertado ({len(chunk)} registros)")
            else:
                logger.error(f"[WEBHOOK] Falha no chunk {chunk_num}/{total_chunks}")

        logger.info(f"[WEBHOOK] Sync de '{table}' concluído: {len(batch)} registros processados.")

    except Exception as e:
        logger.error(f"[WEBHOOK] Erro durante sync de '{table}': {e}")


def _verify_signature(body: bytes, signature_header: str | None) -> bool:
    """Valida a assinatura HMAC-SHA256 via X-Hub-Signature se o secret estiver configurado."""
    secret = os.getenv("WEBHOOK_SECRET", "")
    if not secret:
        # Sem secret configurado, rejeitar por segurança (configure WEBHOOK_SECRET no .env)
        logger.warning("[WEBHOOK] WEBHOOK_SECRET não configurado. Rejeitando requisição.")
        return False

    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@router.post("/nexus")
async def webhook_nexus(
    request: Request,
    background_tasks: BackgroundTasks,
    table: str = Query(..., description="Nome da tabela alvo no Supabase (ex: nexus_contas_receber)"),
):
    """
    Recebe notificações de INSERT/UPDATE do Nexus e sincroniza a tabela correspondente.
    - table: nexus_contas_receber (ou outras tabelas mapeadas futuramente)
    - Responde 202 imediatamente; o sync acontece em background.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature")

    # Valida assinatura HMAC (se WEBHOOK_SECRET estiver no .env)
    if not _verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida.")

    # Verifica se a tabela é suportada
    if table not in TABLE_SOURCE_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"Tabela '{table}' não suportada. Opções: {list(TABLE_SOURCE_MAP.keys())}",
        )

    # Dispara o sync em background e retorna imediatamente
    background_tasks.add_task(_sync_table, table)
    logger.info(f"[WEBHOOK] Sync agendado em background para '{table}'.")

    return {"status": "accepted", "table": table, "message": "Sync agendado."}
