# Stage 1: Build the React Frontend
FROM node:22-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Build the FastAPI Backend (python:3.13-slim - constitutional rule)
FROM python:3.13-slim

WORKDIR /app

# System deps for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy shared dependencies needed for agent nodes
COPY rover_tools/ ./rover_tools/
COPY utils/ ./utils/
COPY agents.py config.py ./

# Copy full backend directory (preserves src package structure)
COPY backend/ ./backend/

# Set PYTHONPATH to root /app so shared modules are importable
ENV PYTHONPATH=/app

# Copy React build from stage 1 into backend static dir
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8080
ENV PORT=8080

# Run from /app/backend so src.* imports resolve correctly
WORKDIR /app/backend

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health', timeout=5)" || exit 1

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "75"]
