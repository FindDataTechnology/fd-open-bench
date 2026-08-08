import os

from celery import Celery


def make_celery() -> Celery:
    """Create configured Celery instance."""

    celery_app = Celery(
        "fd_open_bench",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
        include=["app.tasks"],
    )

    celery_app.conf.update(
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max for evaluations
        worker_prefetch_multiplier=1,  # Prevent resource starvation
    )

    return celery_app


celery_app = make_celery()
