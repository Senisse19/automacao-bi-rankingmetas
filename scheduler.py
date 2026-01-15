"""
Agendador Central (Scheduler)
Orquestra a execução dos scripts de automação modular.
"""
import schedule
import time
import sys
from datetime import datetime
from config import SCHEDULE_TIME, UNIDADES_SCHEDULE_TIME, UNIDADES_WEEKLY_TIME

# Importa as automações modulares
from run_unidades import UnidadesAutomation
from run_metas import MetasAutomation
from utils.logger import get_logger

logger = get_logger("scheduler")

def job_unidades_daily():
    """Executa a automação de Unidades: Relatório Diário."""
    logger.info("Iniciando Unidades Daily")
    ua = UnidadesAutomation()
    ua.process_reports(daily=True, weekly=False)

def job_unidades_weekly():
    """Executa a automação de Unidades: Relatório Semanal."""
    logger.info("Iniciando Unidades Weekly")
    ua = UnidadesAutomation()
    ua.process_reports(daily=False, weekly=True)

def job_metas():
    """Executa a automação de Metas (Power BI)."""
    logger.info("Iniciando Metas Automation")
    ma = MetasAutomation()
    ma.run()

def run_schedule():
    """Configura e inicia o loop de agendamento."""
    logger.info(">>> SCHEDULER INICIADO <<<")
    logger.info(f"Unidades Daily:   Seg-Sex às {UNIDADES_SCHEDULE_TIME}")
    logger.info(f"Unidades Weekly:  Segunda às {UNIDADES_WEEKLY_TIME}")
    logger.info(f"Metas Reports:    Seg-Sex às {SCHEDULE_TIME}")
    
    # Unidades Daily (Mon-Fri)
    schedule.every().monday.at(UNIDADES_SCHEDULE_TIME).do(job_unidades_daily)
    schedule.every().tuesday.at(UNIDADES_SCHEDULE_TIME).do(job_unidades_daily)
    schedule.every().wednesday.at(UNIDADES_SCHEDULE_TIME).do(job_unidades_daily)
    schedule.every().thursday.at(UNIDADES_SCHEDULE_TIME).do(job_unidades_daily)
    schedule.every().friday.at(UNIDADES_SCHEDULE_TIME).do(job_unidades_daily)
    
    # Unidades Weekly (Monday Only)
    schedule.every().monday.at(UNIDADES_WEEKLY_TIME).do(job_unidades_weekly)
    
    # Metas (Mon-Fri)
    schedule.every().monday.at(SCHEDULE_TIME).do(job_metas)
    schedule.every().tuesday.at(SCHEDULE_TIME).do(job_metas)
    schedule.every().wednesday.at(SCHEDULE_TIME).do(job_metas)
    schedule.every().thursday.at(SCHEDULE_TIME).do(job_metas)
    schedule.every().friday.at(SCHEDULE_TIME).do(job_metas)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    if "--now" in sys.argv:
        logger.info(">>> FORÇANDO EXECUÇÃO IMEDIATA (TESTE) <<<")
        job_unidades_daily()
        job_unidades_weekly() # Se for terça, vai rodar igual pra teste
        job_metas()
    else:
        run_schedule()
