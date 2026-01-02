FROM python:3.11-slim

WORKDIR /app

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY *.py .

# Criar diretório para persistência de dados
RUN mkdir -p /app/data

# Variáveis de ambiente (serão sobrescritas pelo docker-compose ou Coolify)
ENV PYTHONUNBUFFERED=1

# Comando padrão: modo monitor
CMD ["python", "main.py", "--monitor"]
