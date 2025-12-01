# -*- coding: utf-8 -*-
"""
workers/celery_app.py
=====================
Celery Configuration für Distributed Task Processing

Architektur:
- Redis als Message Broker und Result Backend
- Separate Queues für verschiedene Task-Typen
- Retry-Logic für fehlerhafte Tasks
- Health Monitoring pro Worker

Author: StratGen Agent V3.8
"""
from celery import Celery
from kombu import Queue, Exchange
import os

# ============================================
# CONFIGURATION
# ============================================

# Redis URL (lokal oder remote)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Worker Konfiguration
WORKER_CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "4"))
TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT", "300"))  # 5 Minuten

# ============================================
# CELERY APP
# ============================================

app = Celery(
    "stratgen",
    broker=REDIS_URL,
    backend=RESULT_BACKEND,
    include=[
        "workers.tasks.llm_tasks",
        "workers.tasks.analysis_tasks",
        "workers.tasks.generation_tasks",
        "workers.tasks.export_tasks",
    ]
)

# ============================================
# QUEUES DEFINITION
# ============================================
# Verschiedene Queues für verschiedene Task-Typen
# Ermöglicht später: GPU-Rechner hört nur auf 'llm' Queue

default_exchange = Exchange("default", type="direct")
llm_exchange = Exchange("llm", type="direct")
analysis_exchange = Exchange("analysis", type="direct")
generation_exchange = Exchange("generation", type="direct")
export_exchange = Exchange("export", type="direct")

app.conf.task_queues = (
    # Default Queue für allgemeine Tasks
    Queue("default", default_exchange, routing_key="default"),
    
    # LLM Queue - für GPU-intensive Tasks
    Queue("llm", llm_exchange, routing_key="llm"),
    Queue("llm.high", llm_exchange, routing_key="llm.high"),  # Priorität
    
    # Analysis Queue - für CPU-intensive Analyse
    Queue("analysis", analysis_exchange, routing_key="analysis"),
    
    # Generation Queue - für Slide-Generierung
    Queue("generation", generation_exchange, routing_key="generation"),
    
    # Export Queue - für PPTX/PDF Export
    Queue("export", export_exchange, routing_key="export"),
)

# ============================================
# TASK ROUTING
# ============================================
# Definiert welcher Task in welche Queue geht

app.conf.task_routes = {
    # LLM Tasks → llm Queue
    "workers.tasks.llm_tasks.*": {"queue": "llm"},
    "workers.tasks.llm_tasks.generate_high_priority": {"queue": "llm.high"},
    
    # Analysis Tasks → analysis Queue
    "workers.tasks.analysis_tasks.*": {"queue": "analysis"},
    
    # Generation Tasks → generation Queue
    "workers.tasks.generation_tasks.*": {"queue": "generation"},
    
    # Export Tasks → export Queue
    "workers.tasks.export_tasks.*": {"queue": "export"},
}

# ============================================
# CELERY CONFIGURATION
# ============================================

app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Europe/Berlin",
    enable_utc=True,
    
    # Task Execution
    task_time_limit=TASK_TIME_LIMIT,
    task_soft_time_limit=TASK_TIME_LIMIT - 30,
    task_acks_late=True,  # Acknowledge nach Completion (nicht bei Start)
    task_reject_on_worker_lost=True,
    
    # Retry Configuration
    task_default_retry_delay=5,  # 5 Sekunden zwischen Retries
    task_max_retries=3,
    
    # Worker Configuration
    worker_prefetch_multiplier=1,  # Nur 1 Task pro Worker vorhalten
    worker_concurrency=WORKER_CONCURRENCY,
    
    # Result Backend
    result_expires=3600,  # Results nach 1 Stunde löschen
    result_extended=True,  # Erweiterte Result-Infos
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error Handling
    task_track_started=True,
    task_publish_retry=True,
)

# ============================================
# BEAT SCHEDULE (Periodic Tasks)
# ============================================

app.conf.beat_schedule = {
    # Health Check alle 30 Sekunden
    "health-check": {
        "task": "workers.tasks.analysis_tasks.health_check",
        "schedule": 30.0,
    },
    # Cleanup alte Results alle 10 Minuten
    "cleanup-results": {
        "task": "workers.tasks.analysis_tasks.cleanup_old_results",
        "schedule": 600.0,
    },
}

# ============================================
# SIGNALS (Event Handlers)
# ============================================

from celery.signals import task_failure, task_success, worker_ready

@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failures für Monitoring."""
    print(f"[TASK FAILED] {sender.name} (ID: {task_id}): {exception}")

@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """Log task success für Monitoring."""
    # Nur bei Debug
    pass

@worker_ready.connect
def handle_worker_ready(sender=None, **kwargs):
    """Worker ist bereit."""
    print(f"[WORKER READY] {sender}")


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_queue_lengths():
    """Gibt die Länge aller Queues zurück."""
    from redis import Redis
    
    redis_client = Redis.from_url(REDIS_URL)
    
    queues = ["default", "llm", "llm.high", "analysis", "generation", "export"]
    lengths = {}
    
    for queue in queues:
        try:
            length = redis_client.llen(queue)
            lengths[queue] = length
        except Exception:
            lengths[queue] = -1
    
    return lengths


def get_active_workers():
    """Gibt Liste aktiver Worker zurück."""
    inspect = app.control.inspect()
    
    active = inspect.active() or {}
    stats = inspect.stats() or {}
    
    workers = []
    for worker_name, worker_stats in stats.items():
        workers.append({
            "name": worker_name,
            "concurrency": worker_stats.get("pool", {}).get("max-concurrency", 0),
            "active_tasks": len(active.get(worker_name, [])),
            "processed": worker_stats.get("total", {})
        })
    
    return workers
