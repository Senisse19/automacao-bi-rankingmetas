# 📤 SharePoint to WhatsApp Automation (Python)

Automação em Python que baixa o arquivo mais recente da pasta **Diretoria** no SharePoint e envia para um grupo do WhatsApp via **Evolution API**.

## 🚀 Instalação

```bash
# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

Edite o arquivo `config.py` com suas credenciais:

```python
# SharePoint
SHAREPOINT_CONFIG = {
    "client_id": "seu-client-id",
    "client_secret": "seu-client-secret",
    "tenant": "seudominio.onmicrosoft.com",
    ...
}

# Evolution API
EVOLUTION_CONFIG = {
    "server_url": "https://sua-evolution-api.com",
    "api_key": "sua-api-key",
    ...
}
```

## 🎯 Execução

### Execução Manual (única vez)

```bash
python main.py
```

### Execução Agendada (diária às 10h)

```bash
python main.py --schedule
```

## 📁 Estrutura

```
├── main.py              # Script principal
├── config.py            # Configurações e credenciais
├── sharepoint_client.py # Cliente Microsoft Graph API
├── evolution_client.py  # Cliente Evolution API
└── requirements.txt     # Dependências
```

## 🔑 Permissões SharePoint

O App Registration no Azure AD precisa das permissões:

- `Sites.Read.All` (Application)
- `Files.Read.All` (Application)

---

**Versão**: 2.0 (Python)
