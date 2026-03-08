from sqlmodel import Session

from app.core.celery import celery_app
from app.db.session import engine
from app.models.designation import Designation
from app.services.designation import list_designations
from app.services.ingestion.job_fetcher import fetch_jobs_for_designation
from app.services.jobs import create_job_records


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def job_fetching_task(self):
    """Background task to fetch jobs for all designations."""

    with Session(engine) as session:
        designations = list_designations(session)

        for desig in designations:
            try:
                jobs = fetch_jobs_for_designation(designation=desig)

                if jobs:
                    create_job_records(jobs, desig.id)

            except Exception as e:
                print(f"Failed for designation {desig.title}: {e}")


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def job_fetching_task_designation(self, designation_id):
    """Background task to fetch jobs for all designations."""
    with Session(engine) as session:
        desig = Designation(id=designation_id)

        try:
            jobs = fetch_jobs_for_designation(designation=desig)
            if jobs:
                create_job_records(jobs, desig.id)

        except Exception as e:
            print(f"Failed for designation {desig.title}: {e}")
