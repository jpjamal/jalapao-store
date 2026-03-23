FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY . .

# ETL no build: gera o banco-semente a partir dos CSVs
RUN python etl_initial_load.py && \
    mkdir -p /app/data_seed && \
    cp /app/data/database.json /app/data_seed/database.json

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# No startup: se o volume estiver vazio, copia o banco-semente.
# Para forçar reset, basta rodar: docker compose down -v && docker compose up --build
ENTRYPOINT ["sh", "-c", "\
    if [ ! -f /app/data/database.json ]; then \
        echo '📦 Primeira execução: copiando banco-semente para o volume...'; \
        cp /app/data_seed/database.json /app/data/database.json; \
    fi && \
    streamlit run app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false \
"]
