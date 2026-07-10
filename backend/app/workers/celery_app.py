"""Celery app placeholder.

ML (body analysis, virtual try-on) runs entirely on-device in the Flutter
client, so there are currently no server-side ML tasks. This Celery app is kept
as a scaffold for any future async work (e.g. email, cleanup jobs). No task
modules are registered, so no worker needs to run for the demo.
"""

from celery import Celery
import os

celery_app = Celery(
    "style_with_us",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
