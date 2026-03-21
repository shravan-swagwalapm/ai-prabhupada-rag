# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY rag_query.py ./

# FAISS indexes are NOT baked into the image (1.1GB).
# They live on the Railway persistent volume at /data/faiss_indexes/
# Upload them post-deploy via: railway volume upload

# Frontend from stage 1
COPY --from=frontend /app/web/out ./web/out

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000

# Single worker — FAISS index uses ~1.25GB RAM; multiple workers would OOM
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
