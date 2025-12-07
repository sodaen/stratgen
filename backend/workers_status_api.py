"""
Workers Status API - Celery/Redis Status für Frontend
"""
from fastapi import APIRouter

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("/status")
async def workers_status():
    """
    Gibt Worker-Status zurück.
    Da wir keine Celery-Worker haben, geben wir einen leeren Status zurück.
    """
    return {
        "celery_available": False,
        "worker_count": 0,
        "queues": {
            "default": 0,
            "generation": 0,
            "export": 0
        },
        "message": "Celery workers not configured - using synchronous processing"
    }
