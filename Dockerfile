FROM python:3.11-slim

WORKDIR /app

# Configurar timezone para Brasília
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY *.py .

# Criar diretório para persistência de dados
RUN mkdir -p /app/data

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Script de inicialização: roda --init e depois --monitor
CMD ["sh", "-c", "python main.py --init && python main.py --monitor"]
