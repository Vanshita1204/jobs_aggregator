"""
Celery utilities.
"""

from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "jobs_aggregator",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)
celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=False,
)
celery_app.autodiscover_tasks(["app.services"])

celery_app.conf.beat_schedule = {
    "fetch-jobs-daily": {
        "task": "app.services.tasks.job_fetching_task",
        "schedule": crontab(hour=3, minute=2),  # once per day
    },
}
