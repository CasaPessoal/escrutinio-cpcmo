# Usa uma imagem Python que já vem otimizada
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências primeiro (melhor para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código fonte
COPY . .

# Comando de arranque
CMD ["python", "main.py"]
