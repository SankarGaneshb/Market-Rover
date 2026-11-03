# ==============================================================================
# STAGE 1: Ephemeral Build & Compilation Environment
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time compiler tools and header packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy lean production requirements and install wheels into dedicated prefix
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# ==============================================================================
# STAGE 2: Minimal Distroless / Slim Production Runtime
# ==============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install minimal dynamic shared runtime libraries only (zero compiler toolchains)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Security: Create non-root system user and group
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -d /app -s /bin/false appuser

# Copy pre-built isolated Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Set environment paths and disable byte-code writing
ENV PATH="/home/appuser/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:$PYTHONPATH"

# Copy application source code with non-root ownership
COPY --chown=appuser:appuser . .


# Retain pre-built frontend distribution assets
COPY --chown=appuser:appuser static/ ./static/


USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1



CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
