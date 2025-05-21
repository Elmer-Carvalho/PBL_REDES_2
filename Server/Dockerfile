FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Criar diretório para o banco de dados
RUN mkdir -p /app/data

# Executar o script de população do banco de dados
RUN python populate_db.py

# Garantir que o banco de dados foi criado e populado
RUN ls -l /app/data/

CMD ["python", "server.py"] 