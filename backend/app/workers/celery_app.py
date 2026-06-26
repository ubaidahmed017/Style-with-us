from celery import Celery
import os

celery_app = Celery(
    "style_with_us",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_app.conf.task_routes = {
    "app.workers.style_analysis.*": {"queue": "style"},
    "app.workers.virtual_tryon.*": {"queue": "tryon"},
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
