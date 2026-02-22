from app.services.ingestion.job_fetcher import fetch_jobs_for_designation
from app.services.jobs import create_job_records
from app.services.designation import list_designations
from sqlmodel import Session
from app.db.session import engine

def job_fetching_task():
    """Background task to fetch jobs for all designations."""
   
    with Session(engine) as session:
        designations = list_designations(session)
    for desig in designations:
        jobs = fetch_jobs_for_designation(designation=desig)
        create_job_records(jobs, desig.id)