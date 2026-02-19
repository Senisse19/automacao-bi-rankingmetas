import os
from datetime import datetime, timedelta


from config import IMAGES_DIR
from core.services.image_generator import ImageGenerator
from core.services.supabase_service import SupabaseService
from core.clients.evolution_client import EvolutionClient
from core.services.job_enricher import JobEnricher
from utils.logger import get_logger

logger = get_logger("jobs_automation")


class JobsAutomation:
    def __init__(self):
        self.image_gen = ImageGenerator()
        self.supabase = SupabaseService()
        self.enricher = JobEnricher()
        self.whatsapp = EvolutionClient()
        os.makedirs(IMAGES_DIR, exist_ok=True)

    def _validate_jobs(self, jobs, label="jobs"):
        """Filtra jobs inválidos ou vazios."""
        valid = []
        for j in jobs:
            # Check ID and Job Title
            if not j.get("id") or not j.get("job"):
                logger.warning(f"   [FILTER] Job removido ({label}): IDs incompletos. Dump: {j}")
                continue
            valid.append(j)

        if len(valid) < len(jobs):
            logger.info(f"   [FILTER] {len(jobs) - len(valid)} jobs inválidos removidos de '{label}'.")
        return valid

    def fetch_jobs(self, start_date, end_date):
        """Fetch jobs from Nexus DB created or cancelled in range."""
        # We need two queries: New Jobs (data_cadastro) and Cancelled (data_cancelamento)

        # New Jobs
        params_new = {
            "data_cadastro": [f"gte.{start_date}T00:00:00", f"lte.{end_date}T23:59:59"],
            "select": "*",
        }
        new_jobs = self.supabase._get("nexus_jobs", params_new)
        logger.info(f"Found {len(new_jobs) if new_jobs else 0} new jobs.")

        # Cancelled Jobs
        params_cnc = {
            "data_cancelamento": [
                f"gte.{start_date}T00:00:00",
                f"lte.{end_date}T23:59:59",
            ],
            "select": "*",
        }
        cnc_jobs = self.supabase._get("nexus_jobs", params_cnc)
        logger.info(f"Found {len(cnc_jobs) if cnc_jobs else 0} cancelled jobs.")

        return new_jobs, cnc_jobs

    def process_reports(
        self,
        daily=True,
        weekly=False,
        recipients=None,
        template_content=None,
        date_override=None,
    ):
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
            except Exception:
                ref_date_display = ref_date

            logger.info(f"Generating DAILY Report for {ref_date}")
            new_jobs, cnc_jobs = self.fetch_jobs(ref_date, ref_date)

            # --- Strict Validation ---
            new_jobs = self._validate_jobs(new_jobs or [], "Daily New")
            cnc_jobs = self._validate_jobs(cnc_jobs or [], "Daily Cancelled")

            # --- PRE-ROUTING ENRICHMENT ---
            logger.info("Enriching jobs data...")
            new_jobs = self.enricher.enrich(new_jobs)
            cnc_jobs = self.enricher.enrich(cnc_jobs)

            # --- ROUTING LOGIC ---

            # 1. Filter Jobs by Type
            # Note: 'job_type' comes from nexus_jobs (via runner.py mapping)
            jobs_tax = [j for j in new_jobs if j.get("job_type") == "TAX"]
            jobs_corp = [j for j in new_jobs if j.get("job_type") == "CORPORATE"]

            # 2. Filter Recipients by Tags
            # Check if recipient matches tag. If NO tags on recipient, they get nothing (unless default logic applies)
            # Directors get EVERYTHING.

            def has_tag(contact, tag):
                tags = contact.get("tags") or []
                # Handle if tags is string (some DBs return '{a,b}') or list
                if isinstance(tags, str):
                    # Basic parsing for postgres array string if needed, but Supabase/PostgREST usually returns list for text[]
                    try:
                        if tags.startswith("{"):
                            tags = tags.strip("{}").split(",")
                    except Exception:
                        pass
                return tag in tags

            recipients_directors = [r for r in recipients if has_tag(r, "jobs_all")]
            # Fallback: if no one has jobs_all but directors exist, maybe warn?
            # For now, strictly use jobs_all to solve the user request.

            recipients_tax = [r for r in recipients if has_tag(r, "tax")]
            recipients_corp = [r for r in recipients if has_tag(r, "corporate")]

            # 3. Generate & Send Reports

            # A) DIRECTOR REPORT (ALL JOBS)
            if (new_jobs or cnc_jobs) and recipients_directors:
                # Directors see ALL new jobs
                path = os.path.join(IMAGES_DIR, f"Relatório de Jobs Diretoria {ref_date}.pdf")
                self.image_gen.generate_jobs_report(
                    new_jobs,
                    cnc_jobs,
                    f"RELATÓRIO DE JOBS (DIRETORIA) - {ref_date_display}",
                    path,
                )
                self._send_report(
                    "Relatório de Jobs (Diretoria)",
                    path,
                    recipients_directors,
                    template_content,
                )

            # B) TAX REPORT
            # Ensure we don't double send if someone has both tags (e.g. Victor might have all tags)
            # But usually receiving both specific and general is fine for admins.
            if jobs_tax and recipients_tax:
                path = os.path.join(IMAGES_DIR, f"Relatório de Jobs TAX {ref_date}.pdf")
                # Only sending new jobs for now, keeping Cancelled separate or included?
                # Logic imply cancelled also needs routing.
                # Let's filter cancelled too.
                cnc_tax = [j for j in cnc_jobs if j.get("job_type") == "TAX"]

                self.image_gen.generate_jobs_report(
                    jobs_tax,
                    cnc_tax,
                    f"RELATÓRIO DE JOBS (TAX) - {ref_date_display}",
                    path,
                )
                self._send_report("Relatório de Jobs (Tax)", path, recipients_tax, template_content)

            # C) CORPORATE REPORT
            if jobs_corp and recipients_corp:
                path = os.path.join(IMAGES_DIR, f"Relatório de Jobs CORPORATE {ref_date}.pdf")
                cnc_corp = [j for j in cnc_jobs if j.get("job_type") == "CORPORATE"]

                self.image_gen.generate_jobs_report(
                    jobs_corp,
                    cnc_corp,
                    f"RELATÓRIO DE JOBS (CORPORATE) - {ref_date_display}",
                    path,
                )
                self._send_report(
                    "Relatório de Jobs (Corporate)",
                    path,
                    recipients_corp,
                    template_content,
                )

            logger.info(
                f"Reports processed. General (jobs_all): {len(recipients_directors)}, Tax: {len(jobs_tax)} jobs, Corp: {len(jobs_corp)} jobs."
            )
            if not (new_jobs or cnc_jobs):  # This condition checks if there were no jobs at all
                logger.info("No jobs (new or cancelled) found for daily report.")

        # 2. Weekly Report
        if weekly:
            # Last full week logic
            current_monday = today - timedelta(days=today.weekday())
            start_weekly = (current_monday - timedelta(days=7)).strftime("%Y-%m-%d")
            end_weekly = (current_monday - timedelta(days=1)).strftime("%Y-%m-%d")  # Sunday

            start_display = datetime.strptime(start_weekly, "%Y-%m-%d").strftime("%d/%m/%Y")
            end_display = datetime.strptime(end_weekly, "%Y-%m-%d").strftime("%d/%m/%Y")

            logger.info(f"Generating WEEKLY Report for {start_weekly} to {end_weekly}")

            new_w, cnc_w = self.fetch_jobs(start_weekly, end_weekly)

            # --- Strict Validation ---
            new_w = self._validate_jobs(new_w or [], "Weekly New")
            cnc_w = self._validate_jobs(cnc_w or [], "Weekly Cancelled")

            new_w = self.enricher.enrich(new_w)
            cnc_w = self.enricher.enrich(cnc_w)

            if new_w or cnc_w:
                path_w = os.path.join(IMAGES_DIR, f"Relatório de Jobs Semanal {start_weekly}.pdf")
                self.image_gen.generate_jobs_report(
                    new_w,
                    cnc_w,
                    f"RELATÓRIO DE JOBS SEMANAL - {start_display} a {end_display}",
                    path_w,
                )
                self._send_report("Relatório de Jobs Semanal", path_w, recipients, template_content)
            else:
                logger.info("No jobs found for weekly report.")

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
