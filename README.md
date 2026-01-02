# 📊 Automação SharePoint → WhatsApp

Monitora a pasta **Diretoria** no SharePoint e envia automaticamente novos arquivos para um grupo do WhatsApp via Evolution API.

---

## 🚀 Deploy no Coolify (VPS Hostinger)

### Pré-requisitos

- VPS com Coolify instalado
- Acesso ao repositório GitHub (privado)
- Credenciais do SharePoint e Evolution API

---

### Passo 1: Gerar Deploy Key

No seu servidor (via SSH), gere uma chave SSH:

```bash
ssh-keygen -t ed25519 -C "coolify-deploy" -f ~/.ssh/deploy_key -N ""
```

Copie a chave pública:

```bash
cat ~/.ssh/deploy_key.pub
```

---

### Passo 2: Adicionar Deploy Key no GitHub

1. Acesse: `https://github.com/Senisse19/automacao-bi-rankingmetas/settings/keys`
2. Clique em **"Add deploy key"**
3. Título: `Coolify VPS`
4. Cole a chave pública (do passo anterior)
5. **NÃO** marque "Allow write access"
6. Clique em **"Add key"**

---

### Passo 3: Configurar no Coolify

#### 3.1 Adicionar a Private Key no Coolify

1. No Coolify, vá em **Settings → Private Keys**
2. Clique em **"+ Add"**
3. Nome: `GitHub Deploy Key`
4. Cole a chave **privada** (cat ~/.ssh/deploy_key)
5. Salve

#### 3.2 Criar a Aplicação

1. Vá em **Projects → Seu Projeto → + New**
2. Selecione **"Private Repository (with deploy key)"**
3. Repository URL: `git@github.com:Senisse19/automacao-bi-rankingmetas.git`
4. Branch: `main`
5. Private Key: Selecione `GitHub Deploy Key`
6. Clique em **"Continue"**

#### 3.3 Configurar Build

1. Build Pack: **Dockerfile**
2. Dockerfile Location: `Dockerfile`
3. Clique em **"Continue"**

---

### Passo 4: Configurar Variáveis de Ambiente

No Coolify, vá em **Environment Variables** e adicione:

```env
# SharePoint
SHAREPOINT_CLIENT_ID=75342350-912b-496c-8e37-9db1881a3c7e
SHAREPOINT_CLIENT_SECRET=V538Q~7l6s7VhiCpVtEIP.uFI1a3cZwS6hINCdyK
SHAREPOINT_TENANT=audittecnologia.onmicrosoft.com
SHAREPOINT_SITE_ID=audittecnologia.sharepoint.com,9af1fad3-9d34-4233-af6a-9b80903f5c62,a93d52bb-228d-48c8-9764-ed2ce7caa83a
SHAREPOINT_FOLDER_ID=01RAZX6ORC2JKRXA7ZLRDIEZPGRXKO7TAC

# Evolution API (WhatsApp)
EVOLUTION_SERVER_URL=https://evolution.grupostudio.tec.br
EVOLUTION_API_KEY=1FE27459CF28-42B3-AEB2-57B5EE084B21
EVOLUTION_INSTANCE_NAME=automation indicator
EVOLUTION_GROUP_ID=120363407075752057@g.us

# Configurações
MONITOR_INTERVAL_SECONDS=60
DATA_DIR=/app/data
```

---

### Passo 5: Configurar Volume (Persistência)

No Coolify, em **Storages**, adicione:

| Volume Name       | Mount Path  |
| ----------------- | ----------- |
| `sharepoint-data` | `/app/data` |

Isso mantém o arquivo `known_files.json` entre restarts.

---

### Passo 6: Deploy

1. Clique em **"Deploy"**
2. Aguarde o build completar
3. Verifique os logs para confirmar que está rodando

---

## 📋 Verificar se está funcionando

Nos logs do Coolify, você deve ver:

```
👁️ Iniciando Monitor de Arquivos
✅ Instância 'automation indicator' está conectada
🔄 Monitoramento iniciado. Aguardando novos arquivos...
```

---

## 🔧 Comandos Disponíveis

| Comando                     | Descrição                              |
| --------------------------- | -------------------------------------- |
| `python main.py`            | Envia arquivo mais recente             |
| `python main.py --monitor`  | Monitoramento contínuo (padrão Docker) |
| `python main.py --schedule` | Agendamento diário às 10h              |
| `python main.py --init`     | Inicializa arquivos conhecidos         |

---

## 📝 Mensagem Enviada

Quando um novo arquivo é detectado, ele é enviado com a mensagem:

> 📊 _Consolidação Diária - Metas e Receitas_
>
> Consolidação das metas e receitas realizadas até o dia anterior (D-1), bem como o percentual de atingimento, para conhecimento e acompanhamento da Diretoria.
>
> 📅 Atualizado em: DD/MM/AAAA às HH:MM

---

## 🛠️ Troubleshooting

### Container reiniciando constantemente

- Verifique as variáveis de ambiente
- Confirme que o WhatsApp está conectado na instância Evolution

### Arquivos não sendo detectados

- Verifique se `SHAREPOINT_FOLDER_ID` está correto
- Confirme permissões do App Registration no Azure

### Erro de autenticação SharePoint

- Verifique se o `client_secret` não expirou
- Confirme que as permissões `Sites.Read.All` e `Files.Read.All` estão configuradas

---

## 📄 Licença

Projeto privado - Grupo Studio
