# 📊 Automação SharePoint → WhatsApp

Monitora a pasta **Diretoria** no SharePoint e envia automaticamente novos arquivos para o WhatsApp via Evolution API.

---

## 🚀 Instalação

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar credenciais

Edite o arquivo `config.py` com suas credenciais:

- SharePoint (client_id, client_secret, tenant, site_id, folder_id)
- Evolution API (server_url, api_key, instance_name, group_id)

---

## 📋 Comandos

| Comando                     | Descrição                            |
| --------------------------- | ------------------------------------ |
| `python main.py`            | Envia o arquivo mais recente         |
| `python main.py --monitor`  | Monitora novos uploads continuamente |
| `python main.py --schedule` | Agendamento diário às 10h            |
| `python main.py --init`     | Inicializa arquivos conhecidos       |

---

## 📝 Mensagem Enviada

Quando um novo arquivo é detectado, ele é enviado com a mensagem:

> 📊 _Consolidação Diária - Metas e Receitas_
>
> Consolidação das metas e receitas realizadas até o dia anterior (D-1), bem como o percentual de atingimento, para conhecimento e acompanhamento da Diretoria.

---

## 🔧 Configuração de Destino

Para mudar o destinatário, altere `group_id` em `config.py`:

- **Grupo**: `120363407075752057@g.us`
- **Contato**: `5551998129077@s.whatsapp.net`

---

## 📄 Estrutura

```
├── config.py              # Configurações
├── main.py                # Script principal
├── sharepoint_client.py   # Cliente SharePoint
├── evolution_client.py    # Cliente WhatsApp
├── file_monitor.py        # Monitor de arquivos
├── known_files.json       # Arquivos processados
└── requirements.txt       # Dependências
```
