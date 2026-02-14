import requests
from bs4 import BeautifulSoup
from app.models.designation import Designation
from sqlmodel import Session, select
from app.services.parsers import parse_linkedin_jobs
from app.db.session import engine
from app.models.job import Job


def fetch_linkedin_jobs():
    """Fetch LinkedIn search pages for each Designation in the DB.
    Returns a list of dicts with metadata for each saved HTML file.
    """
    # Query designations using SQLModel session (no .query on model class)
    with Session(engine) as session:
        designations = session.exec(select(Designation)).all()

    results = []
    for designation in designations:
        title = designation.title.replace(" ", "%20")  # URL encode spaces
        linkedin_url = (
            f"https://www.linkedin.com/jobs/search?keywords={title}&location=India&geoId=102713980&f_TPR=r86400&f_JT=F&position=1&pageNum=0"
        )
        response = requests.get(linkedin_url)
        page_data = response.text
        # parse minimally (placeholder for extraction logic)
        soup = BeautifulSoup(page_data, "html.parser")
        linked_jobs = parse_linkedin_jobs(soup)

        # Prepare jobs for insertion: attach designation_id and ensure required fields
        to_insert = []
        for j in linked_jobs:
            job_data = {
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location"),
                "description": j.get("description", ""),
                "source": j.get("source", "LinkedIn"),
                "source_url": j.get("source_url"),
                "designation_id": designation.id,
            }
            if not job_data["source_url"]:
                continue
            to_insert.append(job_data)

        # Insert new jobs into DB, skipping duplicates (by source_url)
        if to_insert:
            with Session(engine) as session:
                for jd in to_insert:
                    exists = session.exec(select(Job).where(Job.source_url == jd["source_url"])).first()
                    if exists:
                        continue
                    job_obj = Job(**jd)
                    session.add(job_obj)
                session.commit()

    return results
