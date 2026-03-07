from bs4 import BeautifulSoup
from sqlmodel import Session

from app.db.session import engine
from app.services.designation import Designation, list_designations
from app.services.fetchers.page_fetcher import fetch_page
from app.services.fetchers.playwright import fetch_page_with_browser
from app.services.parsers import (
    parse_hirist_jobs,
    parse_indeed_jobs,
    parse_linkedin_jobs,
)

# Central definition of sources (VERY IMPORTANT)
SOURCES = {
    "hirist": {
        "url": (
            "https://www.hirist.tech/search/{slug}"
            "?loc=&minexp=0&maxexp=0&posting=3"
            "&ref=homepage&query={title}&sort=&industry="
        ),
        "parser": parse_hirist_jobs,
        "fetcher": fetch_page_with_browser,
    },
    "linkedin": {
        "url": (
            "https://www.linkedin.com/jobs/search"
            "?keywords={title}&location=India&geoId=102713980"
            "&f_TPR=r86400&f_JT=F&position=1&pageNum=0"
        ),
        "parser": parse_linkedin_jobs,
        "fetcher": fetch_page,
    },
    "indeed": {
        "url": (
            "https://in.indeed.com/jobs"
            "?q={title}&l=india&fromage=1"
            "&sc=0kf%3Aattr%28CF3CP%29%3B"
            "&from=searchOnDesktopSerp"
        ),
        "parser": parse_indeed_jobs,
        "fetcher": fetch_page_with_browser,
    },
}


def fetch_jobs_for_designation(
    designation: Designation | None = None,
) -> list[dict]:
    """
    Orchestrates fetching + parsing jobs from all sources.
    Best-effort ingestion: one source failing should not block others.
    """

    all_jobs: list[dict] = []
    for source_name, source in SOURCES.items():
        try:
            title = designation.title.replace(" ", "%20")
            slug = designation.title.replace(" ", "-").lower()
            url = source["url"].format(title=title, slug=slug)
            html = source["fetcher"](url)
            soup = BeautifulSoup(html, "html.parser")
            jobs = source["parser"](soup)
            all_jobs.extend(jobs)
        except Exception:
            # Best-effort ingestion: log later if needed
            continue

    return all_jobs
