# ==============================================================================
# Stage 1: Build Frontend Static Assets (React / Vite)
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app

ENV GENERATE_SOURCEMAP=false
ENV NODE_ENV=production

# Copy package files and build Market Rover Frontend
COPY market_rover/frontend /app/market_rover/frontend
RUN cd /app/market_rover/frontend && npm install --legacy-peer-deps && npm run build

# Copy package files and build HIL Rover Frontend
COPY hil_rover/frontend /app/hil_rover/frontend
RUN cd /app/hil_rover/frontend && npm install --legacy-peer-deps && npm run build

# Copy package files and build InvestBrand Frontend
COPY investbrand/frontend /app/investbrand/frontend
RUN cd /app/investbrand/frontend && npm install --legacy-peer-deps && npm run build

# Organize all compiled static bundles under /app/static and prune sourcemaps
RUN mkdir -p /app/static/market_rover /app/static/hil_rover /app/static/investbrand && \
    cp -r /app/market_rover/frontend/dist/* /app/static/market_rover/ && \
    cp -r /app/hil_rover/frontend/dist/* /app/static/hil_rover/ && \
    cp -r /app/investbrand/frontend/build/* /app/static/investbrand/ || true && \
    find /app/static -name "*.map" -delete || true

# ==============================================================================
# Stage 2: Unified Production Python Application Runtime
# ==============================================================================
FROM python:3.13-slim AS runner
WORKDIR /app

# Install system dependencies & binutils for symbol stripping
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install lean production Python dependencies
COPY requirements-prod.txt /app/requirements-prod.txt
RUN pip install --no-cache-dir --compile -r requirements-prod.txt && \
    pip cache purge 2>/dev/null || true && \
    # Strip binary debug symbols from compiled C-extensions (.so) \
    find /usr/local/lib/python3.13/site-packages -name "*.so" -exec strip --strip-unneeded {} + 2>/dev/null || true && \
    # Remove stub files, test trees, and C headers from site-packages \
    find /usr/local/lib/python3.13/site-packages -name "*.pyi" -delete || true && \
    find /usr/local/lib/python3.13/site-packages -name "*.c" -delete || true && \
    find /usr/local/lib/python3.13/site-packages -name "*.h" -delete || true && \
    find /usr/local/lib/python3.13/site-packages -name "*.cpp" -delete || true && \
    find /usr/local/lib/python3.13/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13/site-packages -type d -name "testing" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local -type f -name '*.pyc' -delete || true && \
    find /usr/local -type f -name '*.pyo' -delete || true && \
    # Purge build tooling from final image to minimize size \
    apt-get purge -y binutils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . /app

# Prune uncompiled frontend source trees, tests, and non-production files
RUN rm -rf /app/market_rover/frontend /app/hil_rover/frontend /app/investbrand/frontend /app/pledge_rover/frontend \
    /app/tests /app/metrics /app/reports /app/output /app/uploads /app/.pytest_cache /app/data/*.db 2>/dev/null || true

# Copy freshly compiled static frontend assets from Stage 1 into /app/static
COPY --from=frontend-builder /app/static /app/static

# Ensure PYTHONPATH includes repo root and satellite module paths
ENV PYTHONPATH="/app:/app/market_rover/backend"
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
