# ==============================================================================
# Stage 1: Build Frontend Static Assets (React / Vite)
# ==============================================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app

ENV GENERATE_SOURCEMAP=false

# 1. Build Market Rover Frontend (Vite SPA)
COPY market_rover/frontend /app/market_rover/frontend
RUN cd /app/market_rover/frontend && npm install --include=dev --legacy-peer-deps && npm run build

# 2. Build HIL Rover Frontend (Vite SPA scoped to /hil/)
COPY hil_rover/frontend /app/hil_rover/frontend
RUN cd /app/hil_rover/frontend && npm install --include=dev --legacy-peer-deps && npm run build

# 3. Build InvestBrand Frontend (React CRA scoped to /investbrand/)
COPY investbrand/frontend /app/investbrand/frontend
RUN cd /app/investbrand/frontend && npm install --include=dev --legacy-peer-deps && npm run build

# 4. Build Pledge Rover Frontend (Vite SPA scoped to /pledge/)
COPY pledge_rover/frontend /app/pledge_rover/frontend
RUN cd /app/pledge_rover/frontend && npm install --include=dev --legacy-peer-deps && npm run build

# Organize all compiled static bundles under /app/static and prune sourcemaps
RUN mkdir -p /app/static/market_rover /app/static/hil_rover /app/static/investbrand /app/static/pledge_rover && \
    cp -r /app/market_rover/frontend/dist/* /app/static/market_rover/ && \
    cp -r /app/hil_rover/frontend/dist/* /app/static/hil_rover/ && \
    cp -r /app/investbrand/frontend/build/* /app/static/investbrand/ || true && \
    cp -r /app/pledge_rover/frontend/dist/* /app/static/pledge_rover/ || true && \
    find /app/static -name "*.map" -delete || true

# ==============================================================================
# Stage 2: Unified Production Python Application Runtime (Ultra-Lean)
# ==============================================================================
FROM python:3.13-slim AS runner
WORKDIR /app

# Install system runtime dependencies & binutils for symbol stripping
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install lean production Python dependencies
COPY requirements-prod.txt /app/requirements-prod.txt
RUN pip install --no-cache-dir --compile -r requirements-prod.txt && \
    # Uninstall heavy unused transitive packages (saves ~220MB) \
    pip uninstall -y scipy kubernetes pyarrow onnxruntime chromadb chromadb_rust_bindings lance pymupdf pdfminer pypdf pypdfium2 docling_parse docutils rapidocr selenium jieba 2>/dev/null || true && \
    pip cache purge 2>/dev/null || true && \
    # Strip binary debug symbols from compiled C-extensions (.so) \
    find /usr/local/lib/python3.13/site-packages -name "*.so" -exec strip --strip-unneeded {} + 2>/dev/null || true && \
    # Remove stub files, test trees, discovery caches, and C headers from site-packages \
    find /usr/local/lib/python3.13/site-packages -type d \( -name "tests" -o -name "test" -o -name "testing" -o -name "doc" -o -name "docs" -o -name "__pycache__" -o -name "discovery_cache" \) -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13/site-packages -name "*.pyi" -o -name "*.c" -o -name "*.h" -o -name "*.cpp" -o -name "*.map" -delete 2>/dev/null || true && \
    find /usr/local -type f -name '*.pyc' -delete || true && \
    find /usr/local -type f -name '*.pyo' -delete || true && \
    # Purge build tooling from final image to minimize size \
    apt-get purge -y binutils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy backend application modules and services specifically
COPY market_rover/backend /app/market_rover/backend
COPY hil_rover/backend /app/hil_rover/backend
COPY investbrand/backend /app/investbrand/backend
COPY pledge_rover/backend /app/pledge_rover/backend
COPY ownerise /app/ownerise
COPY rover_tools /app/rover_tools
COPY utils /app/utils
COPY tabs /app/tabs
COPY data /app/data
COPY server.py /app/server.py
COPY crew_engine.py /app/crew_engine.py
COPY config.py /app/config.py
COPY agents.py /app/agents.py
COPY tasks.py /app/tasks.py

# Install lightweight pure-python scipy stub into site-packages
RUN cp -r /app/rover_tools/stubs/scipy /usr/local/lib/python3.13/site-packages/scipy 2>/dev/null || true

# Copy freshly compiled static frontend assets from Stage 1 into /app/static
COPY --from=frontend-builder /app/static /app/static

# Ensure PYTHONPATH includes repo root, stubs, and satellite module paths
ENV PYTHONPATH="/app:/app/rover_tools/stubs:/app/market_rover/backend"
ENV PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
