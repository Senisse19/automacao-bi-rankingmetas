# Configurações SharePoint
SHAREPOINT_CONFIG = {
    "client_id": "75342350-912b-496c-8e37-9db1881a3c7e",
    "client_secret": "REDACTED",
    "tenant": "audittecnologia.onmicrosoft.com",
    "site_id": "audittecnologia.sharepoint.com,9af1fad3-9d34-4233-af6a-9b80903f5c62,a93d52bb-228d-48c8-9764-ed2ce7caa83a",
    "folder_id": "01RAZX6ORC2JKRXA7ZLRDIEZPGRXKO7TAC",  # Pasta Diretoria
}

# Configurações Power BI (mesmas credenciais do SharePoint)
POWERBI_CONFIG = {
    "client_id": "75342350-912b-496c-8e37-9db1881a3c7e",
    "client_secret": "REDACTED",
    "tenant": "audittecnologia.onmicrosoft.com",
    "workspace_id": "4600324e-148c-4aae-a743-601628c04d29",
    "report_name": "Ranking_Metas",
}

# Configurações Evolution API
EVOLUTION_CONFIG = {
    "server_url": "https://evolution.grupostudio.tec.br",
    "api_key": "1FE27459CF28-42B3-AEB2-57B5EE084B21",
    "instance_name": "automation indicator",
    "group_id": "120363407075752057@g.us",
}

# Configuração de agendamento
SCHEDULE_TIME = "10:00"  # Horário de execução diária

# Configuração de monitoramento
MONITOR_INTERVAL_SECONDS = 60  # Intervalo de verificação (em segundos)

# Mensagem padrão para o relatório
REPORT_CAPTION = """📊 *Consolidação Diária - Metas e Receitas*

Consolidação das metas e receitas realizadas até o dia anterior (D-1), bem como o percentual de atingimento, para conhecimento e acompanhamento da Diretoria.

📅 Atualizado em: {data}"""

