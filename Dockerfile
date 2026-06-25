# 1. Usar uma imagem oficial leve do Python 3.10
FROM python:3.10-slim

# 2. Definir o diretório de trabalho
WORKDIR /app

# 3. Copiar os requisitos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar o restante do código
COPY . .

# 5. Expor a porta 8080
EXPOSE 8080

# 6. Comando para arrancar a aplicação
CMD ["python", "main.py"]
