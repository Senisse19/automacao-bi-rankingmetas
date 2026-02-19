"""
Script de gerenciamento de Jobs no Supabase.
Permite listar, criar e remover definições e agendamentos de jobs.
Foco: Registrar o job 'painel_ina'.
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("manage_jobs")
svc = SupabaseService()


def list_definitions():
    logger.info("📋 Listando Definições de Automação...")
    defs = svc._get("automation_definitions", {"select": "*"})
    for d in defs:
        print(f"  [{d['id']}] Key: {d['key']} | Name: {d['name']}")
    return defs


def list_schedules():
    logger.info("⏰ Listando Agendamentos...")
    scheds = svc.get_active_schedules()
    for s in scheds:
        def_name = s.get("definition", {}).get("name", "Unknown")
        print(f"  [{s['id']}] {s['name']} ({def_name}) | Time: {s['scheduled_time']} | Days: {s['days_of_week']}")


def create_ina_job():
    logger.info("🚀 Criando Job 'painel_ina'...")

    # 1. Verificar/Criar Definição
    defs = svc._get("automation_definitions", {"key": "eq.painel_ina"})
    if defs:
        def_id = defs[0]["id"]
        logger.info(f"✅ Definição 'painel_ina' já existe (ID: {def_id}).")
    else:
        logger.info("Creating definition 'painel_ina'...")
        new_def = {
            "key": "painel_ina",
            "name": "Painel INA - Relatório Diário",
            "description": "Envia resumo de inadimplência e conciliação via WhatsApp.",
            "active": True,
        }
        # Inserir e recuperar ID
        # Nota: SupabaseService.upsert_data não retorna ID facilmente se não for configurado.
        # Vamos usar _post direto se possível ou assumir sucesso e buscar de novo.
        # Como upsert_data usa resolution=merge-duplicates, é seguro.
        svc.upsert_data("automation_definitions", new_def, on_conflict="key")

        # Buscar ID recém criado
        defs = svc._get("automation_definitions", {"key": "eq.painel_ina"})
        if not defs:
            logger.error("❌ Falha ao criar definição.")
            return
        def_id = defs[0]["id"]
        logger.info(f"✅ Definição criada com sucesso (ID: {def_id}).")

    # 2. Criar Agendamento (Schedule)
    # Padrão: 08:30, Seg-Sex (1,2,3,4,5)
    sched_name = "Painel INA - Manhã"
    scheds = svc._get("automation_schedules", {"name": f"eq.{sched_name}"})

    if scheds:
        logger.info(f"✅ Agendamento '{sched_name}' já existe.")
        # Opcional: Atualizar destinatários se necessário
    else:
        logger.info(f"Creating schedule '{sched_name}'...")
        new_sched = {
            "definition_id": def_id,
            "name": sched_name,
            "scheduled_time": "08:30:00",
            "days_of_week": [1, 2, 3, 4, 5],  # Seg a Sex
            "active": True,
            "timezone": "America/Sao_Paulo",
        }
        res = svc.upsert_data(
            "automation_schedules", new_sched
        )  # on_conflict id (auto) não funciona pra insert novo sem ID.
        # upsert_data tenta post. Se não passar ID, cria novo?
        # O método upsert_data usa POST e headers merge-duplicates. Se não tiver constraints unicas além do ID, pode duplicar.
        # Melhor checar se já existe antes (feito acima).
        # Para insert puro, upsert_data funciona.

        if res:
            logger.info("✅ Agendamento criado com sucesso.")
        else:
            logger.error("❌ Falha ao criar agendamento.")

    # 3. Vincular Destinatários (Exemplo: Diretoria)
    # Primeiro precisamos dos IDs dos contatos.
    # Vamos listar contatos 'Victor' para teste.
    logger.info("🔍 Buscando contatos 'Victor'...")
    contacts = svc._get("automation_contacts", {"name": "ilike.%Victor%"})

    if not contacts:
        logger.warning("Nenhum contato 'Victor' encontrado para vincular.")
        return

    # Recarregar schedule para pegar ID
    scheds = svc._get("automation_schedules", {"name": f"eq.{sched_name}"})
    if not scheds:
        return
    sched_id = scheds[0]["id"]

    for c in contacts:
        logger.info(f"Vinculando {c['name']} (ID: {c['id']}) ao agendamento...")
        link = {"schedule_id": sched_id, "contact_id": c["id"]}
        # Tabela de ligação: automation_recipients
        # Chave composta (schedule_id, contact_id) deve ser unica.
        # SupabaseService.upsert_data precisa saber on_conflict.
        # Se não houver constraint explicita no banco, pode duplicar.
        # Vamos tentar insert e ignorar erro se duplicado (ou verificar antes)

        exists = svc._get(
            "automation_recipients",
            {"schedule_id": f"eq.{sched_id}", "contact_id": f"eq.{c['id']}"},
        )

        if not exists:
            svc.upsert_data("automation_recipients", link)
            logger.info("  ✅ Vinculado.")
        else:
            logger.info("  ✅ Já vinculado.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create":
        create_ina_job()
    else:
        list_definitions()
        list_schedules()
        print("\nPara criar o job INA, rode: python modules/ina/manage_jobs.py create")
