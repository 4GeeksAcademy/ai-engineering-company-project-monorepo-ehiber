"""Celery application factory for async background tasks."""

from __future__ import annotations

from celery import Celery

from .config import get_settings

celery_app = Celery("trackflow_api")


def configure_celery() -> Celery:
    settings = get_settings()
    celery_app.conf.update(
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,
        task_default_queue=settings.celery_task_default_queue,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        result_expires=3600,
        task_soft_time_limit=settings.celery_task_soft_time_limit_seconds,
        task_time_limit=settings.celery_task_time_limit_seconds,
        task_always_eager=settings.celery_task_always_eager,
        task_eager_propagates=settings.celery_task_always_eager,
        task_store_eager_result=settings.celery_task_always_eager,
    )
    celery_app.autodiscover_tasks(["trackflow_api.tasks"])
    return celery_app


configure_celery()

# Register task modules on import.
from ..tasks import pipeline as _pipeline_tasks  # noqa: E402,F401
