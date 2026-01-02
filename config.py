"""
Configurações da automação SharePoint -> WhatsApp
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

# Configurações Power BI (mesmas credenciais do SharePoint)
POWERBI_CONFIG = {
    "client_id": os.environ.get("SHAREPOINT_CLIENT_ID", "75342350-912b-496c-8e37-9db1881a3c7e"),
    "client_secret": os.environ.get("SHAREPOINT_CLIENT_SECRET", "REDACTED"),
    "tenant": os.environ.get("SHAREPOINT_TENANT", "audittecnologia.onmicrosoft.com"),
    "workspace_id": os.environ.get("POWERBI_WORKSPACE_ID", "4600324e-148c-4aae-a743-601628c04d29"),
    "report_name": os.environ.get("POWERBI_REPORT_NAME", "Ranking_Metas"),
}

# Configurações Evolution API
EVOLUTION_CONFIG = {
    "server_url": os.environ.get("EVOLUTION_SERVER_URL", "https://evolution.grupostudio.tec.br"),
    "api_key": os.environ.get("EVOLUTION_API_KEY", "1FE27459CF28-42B3-AEB2-57B5EE084B21"),
    "instance_name": os.environ.get("EVOLUTION_INSTANCE_NAME", "automation indicator"),
    "group_id": os.environ.get("EVOLUTION_GROUP_ID", "120363407075752057@g.us"),
}

# Configuração de agendamento
SCHEDULE_TIME = os.environ.get("SCHEDULE_TIME", "10:00")

# Configuração de monitoramento
MONITOR_INTERVAL_SECONDS = int(os.environ.get("MONITOR_INTERVAL_SECONDS", "60"))

# Caminho para arquivos de dados (persistência em Docker)
DATA_DIR = os.environ.get("DATA_DIR", ".")
KNOWN_FILES_PATH = os.path.join(DATA_DIR, "known_files.json")

# Mensagem padrão para o relatório
REPORT_CAPTION = os.environ.get("REPORT_CAPTION", """📊 *Consolidação Diária - Metas e Receitas*

Consolidação das metas e receitas realizadas até o dia anterior (D-1), bem como o percentual de atingimento, para conhecimento e acompanhamento da Diretoria.

📅 Atualizado em: {data}""")
