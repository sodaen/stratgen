import os
bind = "127.0.0.1:8011"
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "300"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "90"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "30"))
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = "info"

threads = int(os.getenv("GUNICORN_THREADS", "2"))

preload_app = True
max_requests = 300
max_requests_jitter = 50
