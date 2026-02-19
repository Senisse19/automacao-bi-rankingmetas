import sys
import os

# Garantir que o diretório raiz está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.jobs_client import JobsClient
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("run_jobs")


def transform_job(item):
    """Mapeia o item do Data Lake para o schema de Nexus Jobs."""
    # id, job, data_cadastro, data_inicio_contrato, data_cancelamento,
    # cliente_id, unidade_id, franqueado_id, modelo_negocio, raw_data

    return {
        "id": item.get("codigo"),
        "job": item.get("job"),
        "data_cadastro": item.get("data_cadastro"),
        "data_inicio_contrato": item.get("data_inicio_contrato"),
        "data_cancelamento": item.get("data_cancelamento"),
        "cliente_id": item.get("codigo_cliente"),
        "unidade_id": item.get("codigo_unidade"),
        "franqueado_id": item.get("codigo_franqueado"),
        "modelo_negocio": item.get("modelo_negocio"),
        # Colunas Estendidas
        "codigo_produto": item.get("codigo_produto"),
        "codigo_checklist": item.get("codigo_checklist"),
        "job_divisao": item.get("job_divisao"),
        "data_entrega": item.get("data_entrega"),
        "prazo_ata": item.get("prazo_ata"),
        "ano_analise_inicial": item.get("ano_analise_inicial"),
        "ano_analise_final": item.get("ano_analise_final"),
        "percentual": item.get("percentual"),
        "percentual_passivo": item.get("percentual_passivo"),
        "motivo_cancelamento": item.get("motivo_cancelamento"),
        "user_cancelamento": item.get("user_cancelamento"),
        "responsavel_comercial": item.get("responsavel_comercial"),
        "responsavel_venda": item.get("responsavel_venda"),
        "user_add": item.get("user_add"),
        "data_recebimento": item.get("data_recebimento"),
        "cnpj": item.get("cnpj"),
        "linha": item.get("linha"),
        "codigo_qualidade": item.get("codigo_qualidade"),
    }


def run():
    client = JobsClient()
    svc = SupabaseService()

    logger.info("--- Iniciando Sincronização de Jobs (Incremental) ---")

    try:
        # 1. Inicializar Paginação
        page = 1
        limit = 500  # Tamanho do lote para busca

        while True:
            # Buscar Página
            logger.info(f"Buscando página {page}...")
            # Precisamos acessar a sessão diretamente para controlar melhor os parâmetros,
            # ou poderíamos refatorar o JobsClient.fetch_all_jobs para gerar páginas.
            # Por enquanto, usaremos a sessão/lógica interna do cliente se possível,
            # mas o JobsClient.fetch_all_jobs busca TUDO de uma vez.
            # Provavelmente devemos modificar o JobsClient para suportar paginação, OU apenas fazer aqui.
            # Faremos aqui por segurança para evitar quebrar outras coisas, acessando as propriedades do cliente.

            url = f"{client.api_url}/jobs/"
            params = {"page": page, "limit": limit}

            try:
                resp = client.session.get(url, headers=client.headers, params=params, timeout=60)
                if resp.status_code != 200:
                    logger.error(f"Failed to fetch page {page}: {resp.status_code}")
                    break

                data = resp.json()
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("results") or data.get("data") or []

                if not items:
                    logger.info("Nenhum item adicional encontrado. Sincronização Concluída.")
                    break

                logger.info(f"Página {page}: Obtidos {len(items)} itens. Processando...")

                # 2. Transformar & Mapear
                transformed = []
                for i in items:
                    if i.get("codigo"):
                        t_job = transform_job(i)

                        # --- LÓGICA DE MAPEAMENTO ---
                        # Mapear 'linha' para 'job_type'
                        # S -> TAX
                        # E -> CORPORATE (mas verificar divisao para garantir)
                        linha = t_job.get("linha")
                        divisao = str(t_job.get("job_divisao") or "").upper()

                        if linha == "S" or "TAX" in divisao:
                            t_job["job_type"] = "TAX"
                        elif linha == "E" or any(
                            tag in divisao
                            for tag in [
                                "ENERGY",
                                "AGRO",
                                "BANK",
                                "FINANCE",
                                "CORPORATE",
                            ]
                        ):
                            t_job["job_type"] = "CORPORATE"
                        else:
                            t_job["job_type"] = "OTHER"

                        transformed.append(t_job)

                # 3. Upsert em Lote
                if transformed:
                    logger.info(f"Fazendo upsert de um lote de {len(transformed)} registros...")
                    # Passamos ignore_duplicates=False (o padrão realiza o merge)
                    result = svc.upsert_data("nexus_jobs", transformed)
                    if not result:
                        logger.error(f"Falha ao fazer upsert do lote na página {page}.")

                # Verificar se chegamos ao fim
                if len(items) < limit:
                    logger.info("Última página alcançada.")
                    break

                page += 1

            except Exception as ex:
                logger.error(f"Erro ao processar página {page}: {ex}")
                # Decidir se continua ou interrompe. Vamos interromper por segurança.
                break

        logger.info("Processo de Sincronização de Jobs Finalizado.")

    except Exception as e:
        logger.error(f"Erro crítico na Sincronização de Jobs: {e}")


if __name__ == "__main__":
    run()
