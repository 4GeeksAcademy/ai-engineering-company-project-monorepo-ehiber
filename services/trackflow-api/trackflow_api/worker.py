"""Celery worker entrypoint: celery -A trackflow_api.worker worker --loglevel=info"""

from trackflow_api.core.celery_app import celery_app, configure_celery

configure_celery()

__all__ = ["celery_app"]
