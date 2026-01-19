# Usar imagem leve do Python
FROM python:3.10-slim

# Configurar variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Sao_Paulo

# Instalar dependências do sistema necessárias
# tzdata para fuso horário correto
# gcc e outros para compilar bibliotecas se necessário (ex: Pillow)
RUN apt-get update && apt-get install -y \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Criar diretório para persistência de imagens (volume)
RUN mkdir -p images

# Comando para iniciar a aplicação
CMD ["python", "scheduler.py"]
