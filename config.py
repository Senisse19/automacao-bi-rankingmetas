"""
Configurações da automação Power BI & Nexus -> WhatsApp
Suporta variáveis de ambiente para deploy em Docker/Coolify
"""
import os
import json
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# --- LOAD EXTERNAL SETTINGS ---
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "data", "settings.json")
SETTINGS = {
    "model_map": {},
    "nexus_type_map": {},
    "unidades_type_map": {},
    "departamentos": [],
    "display_names": {}
}

try:
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        SETTINGS.update(loaded)
except Exception as e:
    print(f"CRITICAL WARNING: Could not load data/settings.json: {e}")

# Helper to convert string keys to int (JSON doesn't support int keys)
def _int_keys(d):
    return {int(k): v for k, v in d.items()}

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
POWERBI_CONFIG = {
    "client_id": os.getenv("SHAREPOINT_CLIENT_ID"),
    "client_secret": os.getenv("SHAREPOINT_CLIENT_SECRET"),
    "tenant": os.getenv("SHAREPOINT_TENANT"),
    "workspace_id": os.getenv("POWERBI_WORKSPACE_ID"),
    "dataset_id": os.getenv("POWERBI_DATASET_ID"),
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
    "model_map": _int_keys(SETTINGS["model_map"]),
    "type_map": _int_keys(SETTINGS["nexus_type_map"])
}

# Configurações Unidades (Data Lake)
UNIDADES_CONFIG = {
    "api_url": os.getenv("UNIDADES_API_URL"),
    "token": os.getenv("UNIDADES_TOKEN"),
    "model_map": _int_keys(SETTINGS["model_map"]),
    "type_map": _int_keys(SETTINGS["unidades_type_map"])
}

# Lista de departamentos e Nomes
DEPARTAMENTOS = SETTINGS["departamentos"]
DISPLAY_NAMES = SETTINGS["display_names"]

# Agendamento
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "14:00")
UNIDADES_SCHEDULE_TIME = os.getenv("UNIDADES_SCHEDULE_TIME", "09:30")
UNIDADES_WEEKLY_TIME = os.getenv("UNIDADES_WEEKLY_TIME", "09:30")

# Configuração de monitoramento SharePoint
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "60"))

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

# Destinatários (WhatsApp) - Carregamento legado mantido mas preparado para Supabase
DESTINATARIOS_WHATSAPP = {}
try:
    contacts_path = os.path.join(os.path.dirname(__file__), "contacts.json")
    if os.path.exists(contacts_path):
        with open(contacts_path, "r", encoding="utf-8") as f:
            DESTINATARIOS_WHATSAPP = json.load(f)
except Exception as e:
    print(f"Warning: Could not load contacts.json: {e}")

# Mapeamento de emails (Derivado de WhatsApp por enquanto)
EMAILS_DESTINO = {}
for departamento, lista_contatos in DESTINATARIOS_WHATSAPP.items():
    EMAILS_DESTINO[departamento] = [
        c for c in lista_contatos if "email" in c and c["email"]
    ]

# Mensagem padrão
METAS_CAPTION = os.getenv("METAS_CAPTION", """📊 Acompanhamento Metas Caixa Grupo Studio

Dados consolidados até {data} (D-1).

🎯 Acompanhe o progresso:

https://bi.grupostudio.tec.br/""")

# Admin Settings
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "5551998129077@s.whatsapp.net")
