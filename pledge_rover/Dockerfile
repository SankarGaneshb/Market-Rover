# Stage 1: Build the React Frontend
FROM node:22-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build the FastAPI Backend
FROM python:3.11-slim

WORKDIR /app

# Install Backend Dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy entire backend directory to preserve structure (config, src, etc.)
COPY backend/ ./backend/

# Copy frontend build output from stage 1 into the backend container
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose Cloud Run port
EXPOSE 8080
ENV PORT=8080

# Run from /app so import paths work correctly (backend.src.server)
WORKDIR /app

# ✅ Add health check with extended startup period for database initialization
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# ✅ Add --timeout-keep-alive for Cloud Run compatibility
CMD ["uvicorn", "backend.src.server:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "75"]
