FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY app ./app
COPY api ./api
COPY agents ./agents
COPY schemas ./schemas
COPY scripts ./scripts
COPY sandbox ./sandbox
COPY .env .


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
