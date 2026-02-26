# ============================================
# Stage 1: Build (install dependencies)
# ============================================
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies for compiled packages (psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim
WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Security: run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Health check — liveness endpoint always returns 200 if process is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

# Production entrypoint with gunicorn + UvicornWorker (ASGI)
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
