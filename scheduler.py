
"""
Agendador Central (Scheduler)
Orquestra a execução dos scripts de automação modular via Supabase.
Refatorado para usar LockManager e JobService.
"""
import schedule
import time
import sys
import os

from core.services.supabase_service import SupabaseService
from core.services.job_service import JobService
from core.jobs import JOB_MAPPING, safe_run_job
from utils.lock_manager import LockManager
from utils.logger import get_logger

logger = get_logger("scheduler")

def refresh_schedule():
    """Lê agendamentos do Supabase e atualiza o schedule."""
    logger.info("🔄 Atualizando agendamentos do Supabase...")
    
    # Limpa agendamentos anteriores
    schedule.clear()
    
    # Re-agendar o refresh (a cada 5 minutos)
    schedule.every(5).minutes.do(refresh_schedule)
    
    svc = SupabaseService()
    active_schedules = svc.get_active_schedules()
    
    if not active_schedules:
        logger.warning("Nenhum agendamento ativo encontrado no Supabase.")
    
    count = 0
    # Map ints to schedule library methods (JS Sunday=0 to Python lib)
    day_map = {
        0: 'sunday', 1: 'monday', 2: 'tuesday', 3: 'wednesday',
        4: 'thursday', 5: 'friday', 6: 'saturday', 7: 'sunday'
    }

    for sched in active_schedules:
        try:
            name = sched['name']
            time_str = sched['scheduled_time'] # Expecting "HH:MM:SS"
            days = sched['days_of_week'] or []
            
            def_key = sched['definition']['key']
            job_func = JOB_MAPPING.get(def_key)
            
            if not job_func:
                logger.warning(f"  [SKIP] Definição desconhecida '{def_key}' para schedule '{name}'")
                continue
            
            recipients = sched['recipients']
            if not recipients:
                logger.warning(f"  [SKIP] Schedule '{name}' sem destinatários ativos.")
                continue

            # Resolve Template Content
            template_content = None
            if sched.get('template') and sched['template'].get('content'):
                template_content = sched['template']['content']
            elif sched.get('definition') and sched['definition'].get('default_template') and sched['definition']['default_template'].get('content'):
                template_content = sched['definition']['default_template']['content']
                
            # Parse time "14:00:00" -> "14:00"
            time_clean = ":".join(time_str.split(":")[:2])
            
            # Register for each day
            for d_int in days:
                day_name = day_map.get(int(d_int))
                if day_name:
                    scheduler_obj = getattr(schedule.every(), day_name)
                    # Pass template_content to safe_run_job wrapper
                    scheduler_obj.at(time_clean).do(safe_run_job, job_func, recipients=recipients, template_content=template_content)
                    count += 1
                    
            logger.info(f"  [OK] Agendado '{name}' ({def_key}) às {time_clean} em {days}")
            
        except Exception as e:
            logger.error(f"  [ERRO] Falha ao processar schedule {sched.get('name')}: {e}")

    logger.info(f"✅ Total de jobs agendados: {count}")

def run_scheduler_loop():
    """Loop principal."""
    logger.info(">>> SCHEDULER (V2) INICIADO <<<")
    
    # 1. Acquire Lock
    lock_manager = LockManager()
    if not lock_manager.acquire():
        return

    # 2. Initial Load
    refresh_schedule()
    
    # 3. Setup Job Service
    job_service = JobService()

    logger.info("🚀 Aguardando jobs...")
    
    try:
        while True:
            schedule.run_pending()
            
            # Process Queue
            job_service.check_queue()
            
            # Update Lock Heartbeat
            lock_manager.update_heartbeat()
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Parando Scheduler...")
    except Exception as e:
        logger.critical(f"CRITICAL SCHEDULER ERROR: {e}")
    finally:
        lock_manager.release()

if __name__ == "__main__":
    if "--test-all" in sys.argv:
        logger.info(">>> MODO TESTE IMEDIATO <<<")
        svc = SupabaseService()
        active = svc.get_active_schedules()
        for sched in active:
            key = sched['definition']['key']
            func = JOB_MAPPING.get(key)
            if func:
                logger.info(f"Executando {key}...")
                safe_run_job(func, recipients=sched['recipients'])
    else:
        run_scheduler_loop()
