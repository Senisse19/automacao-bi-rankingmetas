"""
Configurações da automação Power BI & Nexus -> WhatsApp
Suporta variáveis de ambiente para deploy em Docker/Coolify
"""
import os
import json
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

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
    "model_map": {
        1: "Studio Fiscal",
        2: "Studio Law",
        3: "Studio Brokers",
        4: "E-Fiscal",
        5: "Braga & Monteiro",
        6: "SF Braga",
        7: "Studio Alimentos",
        8: "Studio Collection",
        9: "Studio Law II",
        10: "SF Gonzalo",
        11: "SF Claudio",
        12: "E-Contabil",
        13: "Studio Corporate",
        14: "SCI",
        15: "Audit Tecnologia",
        16: "Studio Agro",
        17: "Studio Energy",
        18: "Economix",
        19: "Spacew",
        20: "Banana",
        21: "Studio Assessoria Financeira",
        22: "Studio Par",
        23: "Studio Family Business",
        24: "Studio Adm",
        25: "Studio Log",
        26: "Studio Grow",
        27: "Studio Revisão Bancária",
        28: "Studio X",
        29: "GS Educação",
        30: "Studio RH",
        31: "Loja",
        32: "Studio Bank",
        33: "Studio Law Litigation",
        34: "Exohub",
        35: "Orb",
        36: "EF Comercial",
        37: "SF Comercial",
        38: "SL Comercial",
        39: "Studio Management",
        40: "Studio Store",
        41: "Studio Varejo",
        42: "Studio Contabilidade",
        43: "SBS Store",
    },
    "type_map": {
        1: "Franquia",
        2: "Licença",
        3: "Parceria",
    }
}

# Configurações Unidades (Data Lake)
UNIDADES_CONFIG = {
    "api_url": os.getenv("UNIDADES_API_URL"),
    "token": os.getenv("UNIDADES_TOKEN"),
    "model_map": {
        1: "Studio Fiscal",
        2: "Studio Law",
        3: "Studio Brokers",
        4: "E-Fiscal",
        5: "Braga & Monteiro",
        6: "SF Braga",
        7: "Studio Alimentos",
        8: "Studio Collection",
        9: "Studio Law II",
        10: "SF Gonzalo",
        11: "SF Claudio",
        12: "E-Contabil",
        13: "Studio Corporate",
        14: "SCI",
        15: "Audit Tecnologia",
        16: "Studio Agro",
        17: "Studio Energy",
        18: "Economix",
        19: "Spacew",
        20: "Banana",
        21: "Studio Assessoria Financeira",
        22: "Studio Par",
        23: "Studio Family Business",
        24: "Studio Adm",
        25: "Studio Log",
        26: "Studio Grow",
        27: "Studio Revisão Bancária",
        28: "Studio X",
        29: "GS Educação",
        30: "Studio RH",
        31: "Loja",
        32: "Studio Bank",
        33: "Studio Law Litigation",
        34: "Exohub",
        35: "Orb",
        36: "EF Comercial",
        37: "SF Comercial",
        38: "SL Comercial",
        39: "Studio Management",
        40: "Studio Store",
        41: "Studio Varejo",
        42: "Studio Contabilidade",
        43: "SBS Store",
    },
    "type_map": {
        1: "Franquia",
        2: "TAX",
        3: "Corporate",
        4: "Segmento",
        5: "Platinum",
        6: "GS Partner",
        7: "Flagship",
        8: "JV",
        9: "XP",
        10: "BTG",
        11: "Safra",
        12: "Parceiros",
        13: "NTW",
        14: "Rede de Distribuição B2C",
        15: "PAR",
        16: "PJ360",
        17: "Flagship",
    }
}

# Mapeamento de destinatários individuais por departamento
# Preencha com os números no formato internacional: 55 + DDD + Numero
# Carregar destinatários do JSON
DESTINATARIOS_WHATSAPP = {}
try:
    contacts_path = os.path.join(os.path.dirname(__file__), "contacts.json")
    with open(contacts_path, "r", encoding="utf-8") as f:
        DESTINATARIOS_WHATSAPP = json.load(f)
except Exception as e:
    print(f"Warning: Could not load contacts.json: {e}")
    DESTINATARIOS_WHATSAPP = {}

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

# Mapeamento de emails
# Mapeamento de emails
EMAILS_DESTINO = {}
# Copia a estrutura de DESTINATARIOS_WHATSAPP mas filtrando quem tem email
for departamento, lista_contatos in DESTINATARIOS_WHATSAPP.items():
    EMAILS_DESTINO[departamento] = [
        c for c in lista_contatos if "email" in c and c["email"]
    ]

# Mensagem padrão
METAS_CAPTION = os.getenv("METAS_CAPTION", """📊 Acompanhamento Metas Caixa Grupo Studio

Dados consolidados até {data} (D-1).

🎯 Acompanhe o progresso:

https://bi.grupostudio.tec.br/""")

# Telefone do Admin para alertas de erro (padrão: seu número)
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "5551998129077@s.whatsapp.net")
