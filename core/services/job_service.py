
import time
import json
from core.services.supabase_service import SupabaseService
from core.jobs import JOB_MAPPING, safe_run_job
from utils.logger import get_logger

logger = get_logger("job_service")

class JobService:
    """
    Serviço responsável por processar a fila de jobs (automation_queue) do Supabase.
    """
    def __init__(self):
        self.supabase = SupabaseService()

    def check_queue(self):
        """Verifica e executa jobs da fila."""
        try:
            jobs = self.supabase.get_pending_jobs()
            
            if not jobs:
                return

            for job in jobs:
                self._process_single_job(job)
                    
        except Exception as e:
            logger.error(f"❌ Erro no loop de verificação da fila: {e}")

    def _process_single_job(self, job):
        job_id = job['id']
        logger.info(f"🚀 [QUEUE] Processando Job {job_id}...")
        self.supabase.update_job_status(job_id, "processing")
        self.supabase.log_event("job_queue_start", {"job_id": job_id, "schedule_id": job.get('schedule_id')})
        
        start_time = time.time()
        try:
            # 1. Parse Payload
            payload = job['payload']
            # Handle string payload if needed (though Supabase returns JSON usually)
            if isinstance(payload, str):
                payload = json.loads(payload)
                
            recipients = payload.get('recipients')
            template_content = payload.get('template_content')
            
            # 2. Determine Job Type
            schedule_id = job.get('schedule_id')
            def_key = None
            
            if schedule_id:
                sched_data = self.supabase.get_schedule_by_id(schedule_id)
                if sched_data and sched_data.get('definition'):
                    def_key = sched_data['definition']['key']
            
            if not def_key:
                raise Exception("Não foi possível identificar a definição da automação (schedule_id inválido ou ausente)")
            
            job_func = JOB_MAPPING.get(def_key)
            if not job_func:
                    raise Exception(f"Job desconhecido: {def_key}")
                    
            # 3. Execute
            logger.info(f"  > Executando lógica para: {def_key}")
            safe_run_job(job_func, recipients=recipients, template_content=template_content)
            
            duration = round(time.time() - start_time, 2)
            self.supabase.update_job_status(job_id, "completed", logs=f"Executado com sucesso via Queue em {duration}s")
            self.supabase.log_event("job_queue_success", {"job_id": job_id, "duration": duration, "def_key": def_key})
            logger.info(f"✅ [QUEUE] Job {job_id} concluído em {duration}s.")
            
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            logger.error(f"❌ [QUEUE] Falha no Job {job_id}: {e}")
            self.supabase.update_job_status(job_id, "failed", logs=str(e))
            self.supabase.log_event("job_queue_error", {"job_id": job_id, "error": str(e), "duration": duration}, level="error")
