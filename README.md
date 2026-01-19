# 📊 Automação Power BI & Nexus → WhatsApp

Solução automatizada modular que envia relatórios de Metas (Power BI) e Movimentações de Unidades (Nexus) para grupos corporativos no WhatsApp.

---

## 🚀 Arquitetura Modular

O sistema foi refatorado para maior estabilidade e escalabilidade, dividido em:

1.  **`run_unidades.py`**: Relatórios de Unidades (Nexus). Indepedente do Power BI.
2.  **`run_metas.py`**: Relatórios de Metas (Power BI). Independente do Nexus.
3.  **`scheduler.py`**: Orquestrador central que gerencia os agendamentos de ambos.

---

## ⚙️ Configuração

Edite o arquivo `config.py` para definir credenciais e horários (`SCHEDULE_TIME`, `UNIDADES_SCHEDULE_TIME`, `UNIDADES_WEEKLY_TIME`).

---

## 🛠️ Como Usar e Comandos

### 1. Executar Agendador (Modo Servidor)

Inicia o processo que mantém todos os jobs rodando nos horários configurados. Recomenda-se usar este script para produção.

```bash
python scheduler.py
```

### 2. Disparos Manuais (Testes/Forçados)

Você pode rodar cada módulo isoladamente:

**Relatório de Unidades (Nexus):**

```bash
# Diário (D-1)
python run_unidades.py --daily-only

# Semanal (Semana Anterior)
python run_unidades.py --weekly-only

# Hoje (Para testes imediatos)
python run_unidades.py --today

# Apenas Gerar Imagem (Sem Enviar ao WhatsApp)
python run_unidades.py --today --generate-only

# Gerar Relatório Semanal (Apenas Gerar Imagem) - NOVO
python generate_weekly_unidades.py

# Gerar Relatório Diário (Apenas Gerar Imagem) - NOVO
python generate_daily_unidades.py
```

**Relatório de Metas (Power BI):**

```bash
python run_metas.py

# Apenas Gerar Imagem (Sem Enviar)
python run_metas.py --generate-only
```

**Teste Geral (Scheduler):**
Executa todos os jobs definidos no agendador de uma vez só.

```bash
python scheduler.py --now
```

---

## 📂 Estrutura do Projeto

```
├── clients/               # 🔌 Clientes de Integração (API)
│   ├── evolution_client.py
│   ├── email_client.py
│   ├── powerbi_client.py
│   └── unidades_client.py
├── services/              # 🧠 Lógica de Negócios e Geração
│   ├── image_generator.py
│   └── powerbi_data.py
├── run_unidades.py        # 🚀 Executável Unidades
├── run_metas.py           # 🚀 Executável Metas
├── generate_weekly_unidades.py # 🆕 Gerador Semanal (Sem Envio)
├── generate_daily_unidades.py  # 🆕 Gerador Diário (Sem Envio)
├── scheduler.py           # 🕒 Agendador Central
├── config.py              # ⚙️ Configurações
└── images/                # 📂 Saída das imagens
```
