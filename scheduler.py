"""
Agendador Central (Scheduler)
Orquestra a execução dos scripts de automação modular.
Agora integrado ao Supabase para agendamento dinâmico.
"""
import schedule
import time
import sys
from functools import partial
from datetime import datetime

# Importa as automações modulares
from modules.unidades.runner import UnidadesAutomation
from modules.metas.runner import MetasAutomation
from core.services.supabase_service import SupabaseService
from utils.logger import get_logger

logger = get_logger("scheduler")

# --- Job Wrappers ---

def job_unidades_daily(recipients=None, template_content=None):
    """Executa a automação de Unidades: Relatório Diário."""
    logger.info("Iniciando Unidades Daily (Dynamic)")
    SupabaseService().log_event("job_start", {"job": "unidades_daily"})
    ua = UnidadesAutomation()
    # Pass recipients if provided
    ua.process_reports(daily=True, weekly=False, recipients=recipients, template_content=template_content)

def job_unidades_weekly(recipients=None, template_content=None):
    """Executa a automação de Unidades: Relatório Semanal."""
    logger.info("Iniciando Unidades Weekly (Dynamic)")
    SupabaseService().log_event("job_start", {"job": "unidades_weekly"})
    ua = UnidadesAutomation()
    ua.process_reports(daily=False, weekly=True, recipients=recipients, template_content=template_content)

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

# --- Dynamic Scheduling Logic ---

JOB_MAPPING = {
    'metas_diarias': job_metas,
    'unidades': job_unidades_daily, # Default 'unidades' key to Daily
    'unidades_diario': job_unidades_daily,
    'unidades_semanal': job_unidades_weekly,
    'ranking_geral': job_ranking_geral,
}

def safe_run_dynamic(job_func, recipients=None, template_content=None):
    """Wrapper para executar jobs dinâmicos com tratamento de erro e templates."""
    try:
        if recipients:
             # Pass template_content if the job function accepts it (we'll update jobs to accept **kwargs or strict)
             # Ideally all mapped jobs should accept template_content now.
             job_func(recipients=recipients, template_content=template_content)
        else:
             job_func(template_content=template_content)
        SupabaseService().log_event("job_success", {"job": job_func.__name__})
    except Exception as e:
        error_msg = f"❌ Erro na execução de '{job_func.__name__}': {str(e)}"
        logger.error(error_msg)
        SupabaseService().log_event("job_error", {"job": job_func.__name__, "error": str(e)}, level="error")
        alert_admin(error_msg)

def alert_admin(message):
    """Envia alerta de erro para o admin via WhatsApp."""
    try:
        from core.clients.evolution_client import EvolutionClient
        from config import ADMIN_PHONE
        
        evo = EvolutionClient()
        # Override number if defined in config, else use default
        evo.send_text_message(message, number_override=ADMIN_PHONE)
    except Exception as e:
        logger.error(f"Falha ao enviar alerta para admin: {e}")

def refresh_schedule():
    """Lê agendamentos do Supabase e atualiza o schedule."""
    logger.info("🔄 Atualizando agendamentos do Supabase...")
    
    # Limpa agendamentos anteriores para evitar duplicatas, 
    # MAS mantém a tarefa de refresh (que vamos recriar logo em seguida ou manter separada)
    schedule.clear()
    
    # Re-agendar o refresh (a cada 5 minutos)
    schedule.every(5).minutes.do(refresh_schedule)
    
    svc = SupabaseService()
    active_schedules = svc.get_active_schedules()
    
    if not active_schedules:
        logger.warning("Nenhum agendamento ativo encontrado no Supabase.")
    
    count = 0
    for sched in active_schedules:
        try:
            name = sched['name']
            time_str = sched['scheduled_time'] # Expecting "HH:MM:SS"
            days = sched['days_of_week'] # Expecting list of ints [0, 1...] or strings?
            # Adjust mapping based on DB schema. Assuming days_of_week is array of integers (0=Sunday, 1=Monday... or 0=Monday?)
            # Let's assume standard ISO: 1=Mon, 7=Sun or JS 0=Sun.
            # Implementation plan said "int array".
            # Let's check Supabase implementation behavior if possible.
            # Assuming 0=Sunday, 1=Monday, 2=Tuesday... (standard cron/JS)
            
            # Map ints to schedule library methods
            # schedule library: .monday, .tuesday
            day_map = {
                0: 'sunday', 1: 'monday', 2: 'tuesday', 3: 'wednesday',
                4: 'thursday', 5: 'friday', 6: 'saturday', 7: 'sunday'
            }
            
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
            
            # 1. Try Schedule specific template
            if sched.get('template') and sched['template'].get('content'):
                template_content = sched['template']['content']
            # 2. Try Definition default template
            elif sched.get('definition') and sched['definition'].get('default_template') and sched['definition']['default_template'].get('content'):
                template_content = sched['definition']['default_template']['content']
                
            # Parse time "14:00:00" -> "14:00"
            time_clean = ":".join(time_str.split(":")[:2])
            
            # Register for each day
            for d_int in days:
                day_name = day_map.get(int(d_int))
                if day_name:
                    scheduler_obj = getattr(schedule.every(), day_name)
                    # Pass template_content to safe_run_dynamic
                    scheduler_obj.at(time_clean).do(safe_run_dynamic, job_func, recipients=recipients, template_content=template_content)
                    count += 1
                    
            logger.info(f"  [OK] Agendado '{name}' ({def_key}) às {time_clean} em {days}")
            
        except Exception as e:
            logger.error(f"  [ERRO] Falha ao processar schedule {sched.get('name')}: {e}")

    logger.info(f"✅ Total de jobs agendados: {count}")

def check_queue():
    """Verifica e executa jobs da fila (Job Queue Pattern)."""
    try:
        svc = SupabaseService()
        jobs = svc.get_pending_jobs()
        
        if not jobs:
            return

        for job in jobs:
            job_id = job['id']
            logger.info(f"🚀 [QUEUE] Processando Job {job_id}...")
            svc.update_job_status(job_id, "processing")
            svc.log_event("job_queue_start", {"job_id": job_id, "schedule_id": job.get('schedule_id')})
            
            start_time = time.time()
            try:
                # 1. Parse Payload
                payload = job['payload']
                recipients = payload.get('recipients')
                template_content = payload.get('template_content')
                
                # 2. Determine Job Type
                schedule_id = job.get('schedule_id')
                def_key = None
                
                if schedule_id:
                    sched_data = svc.get_schedule_by_id(schedule_id)
                    if sched_data and sched_data.get('definition'):
                        def_key = sched_data['definition']['key']
                
                if not def_key:
                    raise Exception("Não foi possível identificar a definição da automação (schedule_id inválido ou ausente)")
                
                job_func = JOB_MAPPING.get(def_key)
                if not job_func:
                     raise Exception(f"Job desconhecido: {def_key}")
                     
                # 3. Execute
                logger.info(f"  > Executando lógica para: {def_key}")
                safe_run_dynamic(job_func, recipients=recipients, template_content=template_content)
                
                duration = round(time.time() - start_time, 2)
                svc.update_job_status(job_id, "completed", logs=f"Executado com sucesso via Queue em {duration}s")
                svc.log_event("job_queue_success", {"job_id": job_id, "duration": duration, "def_key": def_key})
                logger.info(f"✅ [QUEUE] Job {job_id} concluído em {duration}s.")
                
            except Exception as e:
                duration = round(time.time() - start_time, 2)
                logger.error(f"❌ [QUEUE] Falha no Job {job_id}: {e}")
                svc.update_job_status(job_id, "failed", logs=str(e))
                svc.log_event("job_queue_error", {"job_id": job_id, "error": str(e), "duration": duration}, level="error")
                
    except Exception as e:
        logger.error(f"❌ Erro no loop de verificação da fila: {e}")

def run_scheduler_loop():
    """Loop principal."""
    logger.info(">>> SCHEDULER (DB MODE) INICIADO <<<")
    
    # Carga inicial
    refresh_schedule()

    # --- SINGLE INSTANCE LOCK ---
    import os
    import atexit
    
    LOCK_FILE = "scheduler.lock"
    
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = f.read().strip()
            logger.warning(f"⚠️ Lock file encontrado (PID {pid}). Verificando se processo existe...")
            # Aqui poderíamos checar se o PID está vivo, mas por simplicidade no Windows/Docker
            # vamos assumir que se o arquivo existe, o scheduler já está rodando.
            # Se for um crash anterior, o usuário deve remover o lock manualmente ou reiniciar o container (que não persistirá o lock se não estiver em volume persistente).
            # Mas como o diretório pode ser montado, é melhor avisar e sair.
            logger.critical(f"❌ Scheduler já está rodando (PID {pid}). Abortando execução para evitar duplicidade.")
            # Opcional: Remover e continuar se tiver certeza que é stale, mas é arriscado.
            # Vamos abortar.
            return 
        except Exception:
            pass
            
    # Criar Lock
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
        
    def remove_lock():
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            logger.info("🔓 Lock file removido.")
            
    atexit.register(remove_lock)
    logger.info(f"🔒 Single Instance Lock adquirido (PID {os.getpid()})")
    # ----------------------------
    
    while True:
        try:
            schedule.run_pending()
            check_queue() # Verifica fila a cada iteração
        except Exception as e:
            logger.critical(f"CRITICAL SCHEDULER ERROR: {e}")
            
        time.sleep(5) # Reduzido para 5s para maior responsividade

if __name__ == "__main__":
    if "--test-all" in sys.argv:
        logger.info(">>> MODO TESTE: Executando todos os agendamentos ativos IMEDIATAMENTE <<<")
        svc = SupabaseService()
        active_schedules = svc.get_active_schedules()
        
        if not active_schedules:
            logger.warning("Nenhum agendamento ativo encontrado para teste.")
        
        for sched in active_schedules:
            name = sched['name']
            def_key = sched['definition']['key']
            recipients = sched['recipients']
            
            logger.info(f"--- Executando: {name} ({def_key}) ---")
            
            job_func = JOB_MAPPING.get(def_key)
            if job_func:
                 # Executa diretamente ignorando o horário
                 safe_run_dynamic(job_func, recipients=recipients)
            else:
                 logger.warning(f"  [SKIP] Job desconhecido: {def_key}")
                 
        logger.info(">>> TESTE FINALIZADO <<<")
    else:
        run_scheduler_loop()
