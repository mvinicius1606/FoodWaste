# 1. Base do Python
FROM python:3.11-slim

# 2. Pasta de trabalho interna do container
WORKDIR /app

# 3. Copia da pasta específica e instala as dependências
COPY ./src/ingestao/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. COPIA APENAS A PASTA DE INGESTÃO
COPY ./src/ingestao ./ingestao

# 5. Copia o arquivo .env para a raiz
# Garante que o .env da raiz do projeto vá para a raiz do container (/app)
COPY .env /app/.env

# 6. O COMANDO DO UVICORN
CMD ["uvicorn", "ingestao.ingestaoapi:app", "--host", "0.0.0.0", "--port", "8000"]