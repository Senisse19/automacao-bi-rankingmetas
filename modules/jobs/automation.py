import os
import sys
from datetime import datetime, timedelta
import json

# Fix path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import IMAGES_DIR
from core.services.image_generator import ImageGenerator
from core.services.supabase_service import SupabaseService
from core.clients.evolution_client import EvolutionClient
from utils.logger import get_logger

logger = get_logger("jobs_automation")

class JobsAutomation:
    def __init__(self):
        self.image_gen = ImageGenerator()
        self.supabase = SupabaseService()
        self.whatsapp = EvolutionClient()
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def fetch_jobs(self, start_date, end_date):
        """Fetch jobs from Nexus DB created or cancelled in range."""
        # We need two queries: New Jobs (data_cadastro) and Cancelled (data_cancelamento)
        
        # New Jobs
        params_new = {
            "data_cadastro": [f"gte.{start_date}T00:00:00", f"lte.{end_date}T23:59:59"],
            "select": "*"
        }
        new_jobs = self.supabase._get("nexus_jobs", params_new)
        logger.info(f"Found {len(new_jobs) if new_jobs else 0} new jobs.")
        
        # Cancelled Jobs
        params_cnc = {
            "data_cancelamento": [f"gte.{start_date}T00:00:00", f"lte.{end_date}T23:59:59"],
            "select": "*"
        }
        cnc_jobs = self.supabase._get("nexus_jobs", params_cnc)
        logger.info(f"Found {len(cnc_jobs) if cnc_jobs else 0} cancelled jobs.")
        
        return new_jobs, cnc_jobs

    def process_reports(self, daily=True, weekly=False, recipients=None, template_content=None, date_override=None):
        logger.info("--- Processing Jobs Reports ---")
        
        today = datetime.now()
        
        # 1. Daily Report
        if daily:
            if date_override:
                ref_date = date_override
            else:
                days_back = 3 if today.weekday() == 0 else 1
                ref_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            # Format date for display: YYYY-MM-DD -> DD/MM/YYYY
            try:
                ref_date_display = datetime.strptime(ref_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                ref_date_display = ref_date

            logger.info(f"Generating DAILY Report for {ref_date}")
            new_jobs, cnc_jobs = self.fetch_jobs(ref_date, ref_date)
            
            # Generate Report NEW
            if new_jobs:
                path_new = os.path.join(IMAGES_DIR, f"Relatório de Novos Jobs Diário {ref_date}.pdf")
                self.image_gen.generate_jobs_report(new_jobs, f"NOVOS JOBS - {ref_date_display}", path_new)
                self._send_report("Novos Jobs Diário", path_new, recipients, template_content)
            else:
                logger.info("No new jobs found for daily report.")

            # Generate Report CANCELLED
            if cnc_jobs:
                path_cnc = os.path.join(IMAGES_DIR, f"Relatório de Jobs Cancelados Diário {ref_date}.pdf")
                self.image_gen.generate_jobs_report(cnc_jobs, f"JOBS CANCELADOS - {ref_date_display}", path_cnc)
                self._send_report("Jobs Cancelados Diário", path_cnc, recipients, template_content)

        # 2. Weekly Report
        if weekly:
            # Last full week logic
            current_monday = today - timedelta(days=today.weekday())
            start_weekly = (current_monday - timedelta(days=7)).strftime("%Y-%m-%d")
            end_weekly = (current_monday - timedelta(days=1)).strftime("%Y-%m-%d") # Sunday
            
            start_display = datetime.strptime(start_weekly, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_display = datetime.strptime(end_weekly, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            logger.info(f"Generating WEEKLY Report for {start_weekly} to {end_weekly}")
            
            new_w, cnc_w = self.fetch_jobs(start_weekly, end_weekly)
            
            if new_w:
                path_w_new = os.path.join(IMAGES_DIR, f"Relatório de Novos Jobs Semanal {start_weekly}.pdf")
                self.image_gen.generate_jobs_report(new_w, f"NOVOS JOBS SEMANAL - {start_display} a {end_display}", path_w_new)
                self._send_report("Novos Jobs Semanal", path_w_new, recipients, template_content)
            
            if cnc_w:
                path_w_cnc = os.path.join(IMAGES_DIR, f"Relatório de Jobs Cancelados Semanal {start_weekly}.pdf")
                self.image_gen.generate_jobs_report(cnc_w, f"JOBS CANCELADOS SEMANAL - {start_display} a {end_display}", path_w_cnc)
                self._send_report("Jobs Cancelados Semanal", path_w_cnc, recipients, template_content)

    def _send_report(self, title, path, recipients, template):
        if not recipients:
            logger.info(f"Generated {path} but no recipients to send.")
            return

        from core.services.notification_service import NotificationService
        notify_service = NotificationService(self.supabase)
        
        caption = f"[JOBS] {title}\nSegue relatório em anexo."
        
        for r in recipients:
             notify_service.send_whatsapp_report(r, path, caption, "jobs")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, help="Override date YYYY-MM-DD")
    parser.add_argument("--weekly", action="store_true", help="Run weekly")
    args = parser.parse_args()
    
    auto = JobsAutomation()
    auto.process_reports(daily=True, weekly=args.weekly, recipients=[], date_override=args.date)
