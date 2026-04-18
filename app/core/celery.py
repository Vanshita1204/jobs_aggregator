"""
Celery utilities.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "jobs_aggregator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=False,
)
celery_app.autodiscover_tasks(["app.services"])

celery_app.conf.beat_schedule = {
    "fetch-jobs-daily": {
        "task": "app.services.tasks.job_fetching_task",
        "schedule": crontab(hour=0, minute=0),  # once per day
    },
}
