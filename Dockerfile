# Stage 1: Build frontend
FROM node:20-slim AS frontend
WORKDIR /app/web

# Pass NEXT_PUBLIC_ env vars as build args so they're inlined at build time
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID

COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Cache-bust: increment to force rebuild (Railway aggressively caches layers)
ARG CACHE_BUST=4

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

# FAQ pre-rendered answers
COPY data/faq.json ./data/faq.json

# FAISS data (may be LFS pointers — app resolves at startup via GitHub LFS API)
COPY faiss_indexes/ ./faiss_indexes/

# Frontend from stage 1
COPY --from=frontend /app/web/out ./web/out

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000

# Single worker — FAISS index uses ~1.25GB RAM; multiple workers would OOM
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
