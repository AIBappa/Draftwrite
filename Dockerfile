# ─── Multi-stage Dockerfile for Pipeline Author (NiceGUI) ───
# Coolify-ready: health check, port 8080, no dev reload

# ── Stage 1: Builder ──
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies (none needed for pure-Python deps)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.12-slim

# Install curl for Coolify health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH \
    NICEGUI_RELOAD=false \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application code
COPY requirements.txt .
COPY Code/python/ ./Code/python/
COPY launcher.py .
# Create required directories (mounted at runtime with -v)
RUN mkdir -p /app/sessions /app/exports /app/keys

# Expose port for Coolify
EXPOSE 8080

# Health check for Coolify zero-downtime deployments
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run the application
CMD ["python", "launcher.py"]
