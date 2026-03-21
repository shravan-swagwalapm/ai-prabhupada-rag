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

# System deps (git-lfs for resolving LFS pointers at build time)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git git-lfs curl && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY rag_query.py ./

# FAISS data — COPY first, then resolve any LFS pointers
COPY faiss_indexes/ ./faiss_indexes/
COPY .gitattributes ./
# Resolve LFS pointers: if vectors.bin is tiny (<1MB), it's a pointer file
# containing the SHA256 of the actual content. Fetch from GitHub LFS.
RUN VECTORS_SIZE=$(stat -c%s faiss_indexes/vectors.bin 2>/dev/null || echo 0) && \
    META_SIZE=$(stat -c%s faiss_indexes/metadata.json 2>/dev/null || echo 0) && \
    echo "vectors.bin: ${VECTORS_SIZE} bytes, metadata.json: ${META_SIZE} bytes" && \
    if [ "$VECTORS_SIZE" -lt 1000000 ]; then \
      echo "LFS pointer detected for vectors.bin — resolving..." && \
      REPO="shravan-swagwalapm/ai-prabhupada-rag" && \
      for f in vectors.bin metadata.json; do \
        FSIZE=$(stat -c%s "faiss_indexes/$f" 2>/dev/null || echo 0) && \
        if [ "$FSIZE" -lt 1000000 ]; then \
          OID=$(grep "oid sha256:" "faiss_indexes/$f" | cut -d: -f2) && \
          SIZE=$(grep "size " "faiss_indexes/$f" | awk '{print $2}') && \
          echo "Fetching $f (oid=$OID, size=$SIZE)..." && \
          RESP=$(curl -s -X POST "https://github.com/${REPO}.git/info/lfs/objects/batch" \
            -H "Content-Type: application/json" \
            -H "Accept: application/vnd.git-lfs+json" \
            -d "{\"operation\":\"download\",\"objects\":[{\"oid\":\"$OID\",\"size\":$SIZE}]}") && \
          URL=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['objects'][0]['actions']['download']['href'])") && \
          curl -L -o "faiss_indexes/$f" "$URL" && \
          echo "Downloaded $f: $(stat -c%s "faiss_indexes/$f") bytes"; \
        fi; \
      done; \
    else \
      echo "LFS files already resolved"; \
    fi

# Frontend from stage 1
COPY --from=frontend /app/web/out ./web/out

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000

# Single worker — FAISS index uses ~1.25GB RAM; multiple workers would OOM
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
