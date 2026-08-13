# ==============================================================================
# Stage 1: Build Frontend Static Assets (React / Vite)
# ==============================================================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app

# Copy package files and build Market Rover Frontend
COPY market_rover/frontend /app/market_rover/frontend
RUN cd /app/market_rover/frontend && npm install --legacy-peer-deps && npm run build

# Copy package files and build HIL Rover Frontend
COPY hil_rover/frontend /app/hil_rover/frontend
RUN cd /app/hil_rover/frontend && npm install --legacy-peer-deps && npm run build

# Copy package files and build InvestBrand Frontend
COPY investbrand/frontend /app/investbrand/frontend
RUN cd /app/investbrand/frontend && npm install --legacy-peer-deps && npm run build

# Organize all compiled static bundles under /app/static
RUN mkdir -p /app/static/market_rover /app/static/hil_rover /app/static/investbrand && \
    cp -r /app/market_rover/frontend/dist/* /app/static/market_rover/ && \
    cp -r /app/hil_rover/frontend/dist/* /app/static/hil_rover/ && \
    cp -r /app/investbrand/frontend/build/* /app/static/investbrand/ || true

# ==============================================================================
# Stage 2: Unified Production Python Application Runtime
# ==============================================================================
FROM python:3.11-slim AS runner
WORKDIR /app

# Install system dependencies & curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy static frontend assets from Stage 1
COPY --from=frontend-builder /app/static /app/static

# Copy all application code
COPY . /app

# Ensure PYTHONPATH includes repo root and satellite module paths
ENV PYTHONPATH="/app:/app/market_rover/backend:/app/pledge_rover/backend:/app/hil_rover/backend:/app/ownerise/backend"
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
