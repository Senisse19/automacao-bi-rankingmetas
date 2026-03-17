"""
Configurações da automação Power BI & Nexus -> WhatsApp
Suporta variáveis de ambiente para deploy em Docker/Coolify
"""

import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERRO: O pacote 'python-dotenv' não foi encontrado.")
    print("Por favor, execute: pip install python-dotenv")

    # Em ambientes críticos, poderíamos encerrar, mas aqui vamos tentar continuar
    # pois o OS pode já ter as variáveis definidas.
    def load_dotenv(*args, **kwargs):
        pass


# Carregar variáveis do arquivo .env (na raiz do projeto)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path)

# --- CONFIGURATIONS ---

# Configurações SharePoint
SHAREPOINT_CONFIG = {
    "client_id": os.getenv("SHAREPOINT_CLIENT_ID"),
    "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET"),
    "tenant": os.getenv("SHAREPOINT_TENANT"),
    "site_id": os.getenv("SHAREPOINT_SITE_ID"),
    "folder_id": os.getenv("SHAREPOINT_FOLDER_ID"),
}

# Configurações Power BI
# Workspace compartilhado por todos os datasets
POWERBI_CONFIG = {
    "client_id": os.getenv("SHAREPOINT_CLIENT_ID"),
    "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET"),
    "tenant": os.getenv("SHAREPOINT_TENANT"),
    # Workspace único compartilhado por todos os relatórios
    "workspace_id": os.getenv("POWERBI_WORKSPACE_ID"),
    # Dataset ID específico para cada automação (variáveis preferidas)
    "metas_workspace_id": os.getenv("POWERBI_METAS_WORKSPACE_ID", os.getenv("POWERBI_WORKSPACE_ID")),
    "metas_dataset_id": os.getenv("POWERBI_METAS_DATASET_ID"),
    "ina_workspace_id": os.getenv("POWERBI_INA_WORKSPACE_ID", os.getenv("POWERBI_WORKSPACE_ID")),
    "ina_dataset_id": os.getenv("POWERBI_INA_DATASET_ID"),
    "unidades_workspace_id": os.getenv("POWERBI_UNIDADES_WORKSPACE_ID", os.getenv("POWERBI_WORKSPACE_ID")),
    "unidades_dataset_id": os.getenv("POWERBI_UNIDADES_DATASET_ID"),
}

# Configurações Evolution API
EVOLUTION_CONFIG = {
    "server_url": os.getenv("EVOLUTION_SERVER_URL"),
    "api_key": os.getenv("EVOLUTION_API_KEY"),
    "instance_name": os.getenv("EVOLUTION_INSTANCE_NAME"),
}

# Configurações Nexus Data (Data Lake)
NEXUS_CONFIG = {
    "api_url": os.getenv("NEXUS_API_URL"),
    "token": os.getenv("NEXUS_TOKEN"),
}

# Configurações Unidades (Data Lake)
UNIDADES_CONFIG = {
    "api_url": os.getenv("UNIDADES_API_URL"),
    "token": os.getenv("UNIDADES_TOKEN"),
}

# Lista de departamentos e Nomes (Legacy/Unused - Removed)
# DEPARTAMENTOS = []
# DISPLAY_NAMES = {}

# Agendamento
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "14:00")
UNIDADES_SCHEDULE_TIME = os.getenv("UNIDADES_SCHEDULE_TIME", "09:30")
UNIDADES_WEEKLY_TIME = os.getenv("UNIDADES_WEEKLY_TIME", "09:30")

# Configuração de monitoramento SharePoint
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))

# Portal URL (for links)
PORTAL_URL = os.getenv("PORTAL_URL", "https://bi.grupostudio.tec.br")

# Caminho para arquivos de dados
DATA_DIR = os.getenv("DATA_DIR", ".")
KNOWN_FILES_PATH = os.path.join(DATA_DIR, "known_files.json")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

# Configurações de Email
EMAIL_CONFIG = {
    "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.titan.email"),
    "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", 587)),
    "username": os.getenv("EMAIL_USERNAME"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "sender_email": os.getenv("EMAIL_SENDER"),
}

# Destinatários (WhatsApp) - Deprecated (Use Supabase Database)
DESTINATARIOS_WHATSAPP = {}

# Mapeamento de emails (Legacy)
EMAILS_DESTINO = {}

# Mensagem padrão
METAS_CAPTION = os.getenv(
    "METAS_CAPTION",
    """📊 Acompanhamento Metas Caixa Grupo Studio

Dados consolidados até {data} (D-1).

🎯 Acompanhe o progresso:

https://bi.grupostudio.tec.br/""",
)

# Admin Settings
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "")


# --- STARTUP VALIDATION ---

_REQUIRED_VARS = [
    "SHAREPOINT_CLIENT_ID",
    "SHAREPOINT_CLIENT_SECRET",
    "SHAREPOINT_TENANT",
    "EVOLUTION_SERVER_URL",
    "EVOLUTION_API_KEY",
    "EVOLUTION_INSTANCE_NAME",
]

_OPTIONAL_WARN_VARS = [
    "SHAREPOINT_SITE_ID",
    "SHAREPOINT_FOLDER_ID",
    "POWERBI_WORKSPACE_ID",
    "ADMIN_PHONE",
]


def validate_config(strict: bool = True) -> bool:
    """
    Valida variáveis de ambiente obrigatórias.
    strict=True encerra o processo se faltarem variáveis críticas.
    Retorna True se tudo estiver ok.
    """
    from src.core.utils.logger import get_logger  # importação local para evitar ciclo

    _logger = get_logger("config")

    missing = [v for v in _REQUIRED_VARS if not os.getenv(v)]
    if missing:
        _logger.error(f"Variáveis obrigatórias ausentes: {', '.join(missing)}")
        if strict:
            sys.exit(1)
        return False

    for var in _OPTIONAL_WARN_VARS:
        if not os.getenv(var):
            _logger.warning(f"Variável opcional não configurada: {var}")

    return True
