# 1. Usar uma imagem oficial do Python 3.10
FROM python:3.10-slim

# 2. Instalar dependências necessárias para o Flet
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libgconf-2-4 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxinerama1 \
    libxfixes3 \
    libxrandr2 \
    libxcursor1 \
    libxdamage1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# 3. Definir o diretório de trabalho dentro do container
WORKDIR /app

# 4. Copiar os requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o restante do código para o container
COPY . .

# 6. Expor a porta que o Flet vai usar
EXPOSE 8080

# 7. Comando para arrancar a aplicação
# O Flet web corre numa porta específica definida pelo ambiente
CMD ["python", "main.py"]