# 📊 Automação Power BI → WhatsApp (Metas)

Solução automatizada que extrai dados de Metas e Resultados diretamente do modelo semântico do Power BI, gera cards informativos e os distribui para grupos departamentais no WhatsApp via Evolution API.

---

## 🚀 Funcionalidades

- **Extração via DAX**: Consulta dados em tempo real usando a API REST do Power BI (`executeQueries`).
- **Valores D-1**: Filtra dados de realizado até o dia anterior (ou mês atual conforme regra de negócio).
- **Geração de Imagens**: Cria cards visuais personalizados usando biblioteca Pillow (PIL).
- **Distribuição Inteligente**:
  - Card "Geral" com resumo de todos departamentos → Grupo Diretoria.
  - Card individual de cada departamento → Grupo específico (ex: Comercial, Tax, Tecnologia).

---

## 📋 Pré-requisitos

- Python 3.10+
- Conta de Serviço (Service Principal) com acesso ao Workspace do Power BI.
- Evolution API configurada e instância conectada.

### Instalação

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

Edite o arquivo `config.py` para definir:

1. **Credenciais Power BI** (`POWERBI_CONFIG`):

   - Tenant ID, Client ID, Client Secret.
   - Workspace ID e Dataset ID.

2. **Evolution API** (`EVOLUTION_CONFIG`):

   - URL do servidor, API Key e Nome da Instância.

3. **Mapeamento de Grupos** (`GRUPOS_WHATSAPP`):
   - ID dos grupos do WhatsApp para cada departamento.

---

## � Estrutura do Projeto

```
├── metas_automation.py    # 🚀 Script principal (Orquestrador)
├── powerbi_data.py        # 🔍 Extração de dados (DAX Queries)
├── image_generator.py     # 🎨 Geração dos cards visuais
├── evolution_client.py    # 📱 Cliente WhatsApp
├── powerbi_client.py      # 🔐 Autenticação e conexão Power BI
├── config.py              # ⚙️ Configurações e credenciais
└── images/                # 📂 Diretório de saída das imagens geradas
```

---

## 🛠️ Como Usar

### 1. Executar com Agendamento (Padrão)

Inicia o processo e aguarda o horário configurado (09:00 diariamente).

```bash
python metas_automation.py
```

### 2. Executar Imediatamente

Roda todo o fluxo (extração -> geração -> envio) agora mesmo.

```bash
python metas_automation.py --now
```

### 3. Apenas Gerar Imagens

Útil para validar layout e dados sem enviar mensagens.

```bash
python metas_automation.py --generate
```

---

## 📊 Departamentos Monitorados

- Comercial
- Operacional
- Corporate
- Expansão
- Franchising
- Tax
- Tecnologia (antigo PJ)
- Educação
