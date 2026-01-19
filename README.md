# 🚀 Studio Automation Core

Hub de Automação Corporativa para envio de relatórios de **Metas (Power BI)** e **Unidades (Nexus)** via WhatsApp.

> Anteriormente conhecido como `ranking-metas-automation`.

---

## 📦 Arquitetura

O projeto foi refatorado para uma arquitetura modular e escalável:

```
studio-automation-core/
├── core/                 # 🔌 Infraestrutura Compartilhada
│   ├── clients/          # Conectores de API (Evolution, PowerBI, Nexus)
│   └── services/         # Lógica de Negócio (Notificação, Supabase, Imagens)
├── modules/              # 🧩 Domínios de Automação
│   ├── metas/            # Automação de Metas (Power BI)
│   │   └── runner.py
│   └── unidades/         # Automação de Unidades (Nexus)
│       └── runner.py
├── scheduler.py          # 🕒 Orquestrador Central
├── config.py             # ⚙️ Configurações
└── images/               # 📂 Saída das imagens
```

---

## ⚙️ Comandos

### Modo Servidor (Produção)

```bash
python scheduler.py
```

### Disparos Manuais

**Metas (Power BI):**

```bash
python modules/metas/runner.py                # Executar e Enviar
python modules/metas/runner.py --generate-only # Apenas Gerar Imagem
```

**Unidades (Nexus):**

```bash
python modules/unidades/runner.py --daily-only   # Diário
python modules/unidades/runner.py --weekly-only  # Semanal
python modules/unidades/runner.py --generate-only # Apenas Gerar Imagem
```

**Teste Geral:**

```bash
python scheduler.py --test-all
```

---

## 🐳 Docker

```bash
docker-compose up -d --build
```

---

## 📋 Configuração

Edite `.env` com as credenciais do Supabase, Evolution API e Power BI.
