"""
Configurações da automação SharePoint -> WhatsApp e Power BI -> WhatsApp
Suporta variáveis de ambiente para deploy em Docker/Coolify
"""
import os

# Configurações SharePoint
SHAREPOINT_CONFIG = {
    "client_id": os.environ.get("SHAREPOINT_CLIENT_ID", "75342350-912b-496c-8e37-9db1881a3c7e"),
    "client_secret": os.environ.get("SHAREPOINT_CLIENT_SECRET", "REDACTED"),
    "tenant": os.environ.get("SHAREPOINT_TENANT", "audittecnologia.onmicrosoft.com"),
    "site_id": os.environ.get("SHAREPOINT_SITE_ID", "audittecnologia.sharepoint.com,9af1fad3-9d34-4233-af6a-9b80903f5c62,a93d52bb-228d-48c8-9764-ed2ce7caa83a"),
    "folder_id": os.environ.get("SHAREPOINT_FOLDER_ID", "01RAZX6ORC2JKRXA7ZLRDIEZPGRXKO7TAC"),
}

# Configurações Power BI
POWERBI_CONFIG = {
    "client_id": os.environ.get("SHAREPOINT_CLIENT_ID", "75342350-912b-496c-8e37-9db1881a3c7e"),
    "client_secret": os.environ.get("SHAREPOINT_CLIENT_SECRET", "REDACTED"),
    "tenant": os.environ.get("SHAREPOINT_TENANT", "audittecnologia.onmicrosoft.com"),
    "workspace_id": os.environ.get("POWERBI_WORKSPACE_ID", "4600324e-148c-4aae-a743-601628c04d29"),
    "dataset_id": os.environ.get("POWERBI_DATASET_ID", "5f1e9f0f-8388-438d-a0be-6a5e13bb3ce4"),
}

# Configurações Evolution API
EVOLUTION_CONFIG = {
    "server_url": os.environ.get("EVOLUTION_SERVER_URL", "https://evolution.grupostudio.tec.br"),
    "api_key": os.environ.get("EVOLUTION_API_KEY", "1FE27459CF28-42B3-AEB2-57B5EE084B21"),
    "instance_name": os.environ.get("EVOLUTION_INSTANCE_NAME", "automation indicator"),
}

# Mapeamento de departamentos para grupos do WhatsApp
# IDs obtidos automaticamente via Evolution API
GRUPOS_WHATSAPP = {
    # Geral - imagem completa com todos os departamentos
    "diretoria": os.environ.get("GRUPO_DIRETORIA", "120363406578477836@g.us"),
    
    # Grupos por departamento
    "comercial": os.environ.get("GRUPO_COMERCIAL", "120363424554621359@g.us"),
    "operacional": os.environ.get("GRUPO_OPERACIONAL", "120363420901876738@g.us"),
    "expansao": os.environ.get("GRUPO_EXPANSAO", "120363424510427324@g.us"),
    "franchising": os.environ.get("GRUPO_FRANCHISING", "120363424019706255@g.us"),
    "educacao": os.environ.get("GRUPO_EDUCACAO", "120363421821150511@g.us"),
    "tax": os.environ.get("GRUPO_TAX", "120363422634608724@g.us"),
    "corporate": os.environ.get("GRUPO_CORPORATE", "120363420686125971@g.us"),
    "tecnologia": os.environ.get("GRUPO_PJ", "120363421733361621@g.us"),
}

# Lista de departamentos para gerar imagens
DEPARTAMENTOS = [
    "comercial",
    "operacional", 
    "expansao",
    "franchising",
    "educacao",
    "tax",
    "corporate",
    "tecnologia",
]

# Nomes para exibição (com acentos)
DISPLAY_NAMES = {
    "diretoria": "Grupo Studio",
    "comercial": "Comercial",
    "operacional": "Operacional", 
    "expansao": "Expansão",
    "franchising": "Franchising",
    "educacao": "Educação",
    "tax": "Tax",
    "corporate": "Corporate",
    "tecnologia": "Tecnologia",
}

# Agendamento do disparo diário
SCHEDULE_TIME = os.environ.get("SCHEDULE_TIME", "09:00")  # Horário do disparo diário

# Configuração de monitoramento SharePoint (automação existente)
MONITOR_INTERVAL_SECONDS = int(os.environ.get("MONITOR_INTERVAL_SECONDS", "60"))

# Caminho para arquivos de dados
DATA_DIR = os.environ.get("DATA_DIR", ".")
KNOWN_FILES_PATH = os.path.join(DATA_DIR, "known_files.json")
IMAGES_DIR = os.path.join(DATA_DIR, "images")

# Mensagem padrão para o relatório de metas
METAS_CAPTION = os.environ.get("METAS_CAPTION", """📊 *Metas {departamento}*

Dados consolidados até {data} (D-1).

🎯 Acompanhe seu progresso!""")
