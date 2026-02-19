import sys
import os
from datetime import datetime

# Garantir que o diretório raiz está no path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.clients.unidades_client import UnidadesClient
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("run_nexus_sync")


def sync_unidades(client, svc):
    logger.info("--- Sincronizando UNIDADES ---")
    try:
        data = client.fetch_all_from_source("unidades")
        logger.info(f"Encontradas {len(data)} unidades no Nexus.")

        batch = []
        for item in data:
            row = {
                "id": item.get("codigo"),
                "nome": item.get("nome"),
                "cidade": item.get("cidade"),
                "uf": item.get("uf"),
                # Este passo garante a manutenção de uma estrutura flexível.
                "updated_at": datetime.now().isoformat(),
            }
            # Mapeamento dinâmico para todos os outros campos do Nexus
            for k, v in item.items():
                if k not in ["codigo"]:
                    clean_k = k.replace(" ", "_")
                    row[clean_k] = v

            batch.append(row)

        # Upsert
        logger.info(f"Fazendo upsert de {len(batch)} unidades...")
        chunk_size = 500  # Tamanho do lote para o upsert
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i : i + chunk_size]
            success = svc.upsert_data("nexus_unidades", chunk)
            if success:
                logger.info(f"Upserted items {i} to {i + len(chunk)}")
            else:
                logger.error(f"Failed to upsert items {i} to {i + len(chunk)}")

    except Exception as e:
        logger.error(f"Erro ao sincronizar unidades: {e}")


def sync_participantes(client, svc):
    logger.info("--- Sincronizando PARTICIPANTES ---")
    try:
        # UnidadesClient.fetch_all_from_source("participantes") invoca a busca paginada
        data = client.fetch_all_from_source("participantes")
        logger.info(f"Encontrados {len(data)} participantes no Nexus.")

        batch = []
        for item in data:
            row = {
                "id": item.get("id") or item.get("codigo"),
                "nome": item.get("nome"),
                "email": item.get("email"),
                "ativo": item.get("ativo", True),
                "updated_at": datetime.now().isoformat(),
            }
            for k, v in item.items():
                if k not in ["id", "codigo"]:
                    clean_k = k.replace(" ", "_")
                    row[clean_k] = v
            batch.append(row)

        logger.info(f"Fazendo upsert de {len(batch)} participantes...")
        chunk_size = 500
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i : i + chunk_size]
            svc.upsert_data("nexus_participantes", chunk)

    except Exception as e:
        logger.error(f"Erro ao sincronizar participantes: {e}")


def sync_modelos(client, svc):
    logger.info("--- Sincronizando MODELOS (Vendas/Contratos) ---")
    try:
        data = client.fetch_all_from_source("modelos")
        logger.info(f"Encontrados {len(data)} modelos no Nexus.")

        # Busca prévia de IDs de Unidades conhecidas para evitar erros de chave estrangeira (FK)
        # Em uma sincronização bruta estrita, poderíamos apenas fazer o upsert e confiar nas constraints.
        # Mas a lógica do strict_lake_mirror.py incluía o tratamento de fallback para unidades ausentes.
        # Preservamos essa lógica para garantir robustez.

        try:
            known_unit_ids = svc.get_all_ids("nexus_unidades")
            logger.info(f"Unidades conhecidas no DB: {len(known_unit_ids)}")
        except Exception:
            known_unit_ids = set()

        batch = []
        missing_unidade_ids = set()

        for item in data:
            dt_contrato = item.get("data_contrato") or item.get("data")
            if dt_contrato == "":
                dt_contrato = None

            uid = item.get("unidade")

            # Filtro de Dados Legados (< 2024) - Conforme a lógica do strict_lake_mirror.py
            if dt_contrato and dt_contrato < "2024-01-01":
                continue

            if uid and str(uid) not in known_unit_ids:
                missing_unidade_ids.add(str(uid))

            row = {
                "id": item.get("id") or item.get("codigo"),
                "unidade_id": uid,
                "consultor_id": item.get("consultor_venda"),
                "data_contrato": dt_contrato,
                "valor": item.get("valor") or 0,
                "status": "Cancelado" if item.get("cancelamento") == 1 else "Ativo",
                "updated_at": datetime.now().isoformat(),
            }
            # Mapeamento dinâmico
            for k, v in item.items():
                if k not in ["id", "codigo"]:
                    clean_k = k.replace(" ", "_")
                    row[clean_k] = v

            batch.append(row)

        # Tratar Unidades Ausentes (Placeholders)
        if missing_unidade_ids:
            logger.info(
                f"⚠ Encontradas {len(missing_unidade_ids)} unidades referenciadas mas inexistentes. Buscando nomes via API..."
            )
            placeholder_batch = []
            for miss_uid in missing_unidade_ids:
                try:
                    # Tenta buscar o nome real via API do Nexus
                    nome_real = client.fetch_unit_name(int(miss_uid))
                except Exception:
                    nome_real = f"Unidade {miss_uid}"

                placeholder_batch.append(
                    {
                        "id": miss_uid,
                        "nome": nome_real,
                        "cidade": "-",
                        "uf": "-",
                        "raw_data": {"fetched_from_api": True, "original_id": miss_uid},
                        "updated_at": datetime.now().isoformat(),
                    }
                )
                # Adicionar aos conhecidos para evitar re-processamento no loop (SVC trata duplicatas via upsert)
                known_unit_ids.add(miss_uid)

            chunk_size = 500
            for i in range(0, len(placeholder_batch), chunk_size):
                chunk = placeholder_batch[i : i + chunk_size]
                svc.upsert_data("nexus_unidades", chunk)
                logger.info(f"  -> Inserted placeholders {i} - {i + len(chunk)}")

        # Upsert Models
        logger.info(f"Fazendo upsert de {len(batch)} modelos (2024+)...")
        chunk_size = 500
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i : i + chunk_size]
            success = svc.upsert_data("nexus_modelos", chunk)
            if not success:
                logger.error(f"Failed chunk {i}")

    except Exception as e:
        logger.error(f"Erro ao sincronizar modelos: {e}")


def run():
    logger.info("=== Starting Nexus Reference Sync ===")
    client = UnidadesClient()
    svc = SupabaseService()

    sync_unidades(client, svc)
    sync_participantes(client, svc)
    sync_modelos(client, svc)

    # Novos Syncs (Enriquecimento de Jobs)
    from modules.referencial.sync_services import SyncServices
    from modules.referencial.sync_contracts import SyncContracts

    try:
        SyncServices().run()
        SyncContracts().run()
    except Exception as e:
        logger.error(f"Erro nos syncs de enriquecimento: {e}")

    logger.info("=== Nexus Reference Sync Complete ===")


if __name__ == "__main__":
    run()
