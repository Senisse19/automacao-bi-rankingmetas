import threading
import uvicorn
import os
import sys

# Adiciona o diretório atual ao PYTHONPATH para garantir que os imports funcionem
sys.path.append(os.getcwd())

from src.core.api.main import app
from src.apps.scheduler.scheduler import run_scheduler_loop, validate_config

def start_api():
    # Porta 3000: deve coincidir com "Ports Exposes" configurado no Coolify
    print("🚀 Iniciando API na porta 3000...")
    uvicorn.run(app, host="0.0.0.0", port=3000)

def start_scheduler():
    print("⏰ Iniciando Scheduler...")
    try:
        validate_config(strict=True)
        run_scheduler_loop()
    except Exception as e:
        print(f"❌ Erro ao iniciar Scheduler: {e}")

if __name__ == "__main__":
    # Inicia o scheduler em uma thread separada (daemon=True para fechar com o processo principal)
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Inicia a API no processo principal (bloqueante)
    start_api()
