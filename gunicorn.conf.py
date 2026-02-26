import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.getenv('SERVER_PORT', '8000')}"

# Workers — 2 * CPU cores + 1 (async workers handle concurrency per worker)
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Security — prevent oversized requests
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Process naming
proc_name = "app"

# Preload app for faster worker startup and shared memory
preload_app = True
