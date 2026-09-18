"""Portal-specific HTML parsers for the daily/on-demand job search pages.

Each function takes a `BeautifulSoup` object of a search-results page (not a
single job's detail page) and returns a list of dicts with the keys title,
company, location, source, source_url. These are consumed by
`app.services.ingestion.job_fetcher.fetch_jobs_for_designation` and then
deduplicated/persisted by `app.services.jobs.create_job_records`.

The CSS selectors below are tied to each portal's current markup and will
break silently (returning fewer/no jobs) if the portal changes its DOM.
"""

from urllib.parse import urlsplit

from app.core.logging import get_logger
from app.services.external_ingestion import _extract_jk

logger = get_logger(__name__)


def _strip_tracking_params(url: str) -> str:
    """Drop a URL's query string and fragment, leaving the bare path.

    Input: url (str) — a job-detail link straight off a search-results page.
    Output: str — the same URL with everything from `?`/`#` onward removed.

    Calls: none.
    Called by: `parse_linkedin_jobs()`, `parse_hirist_jobs()` (this file).

    Logic: LinkedIn and Hirist search-result links embed session/ranking
        noise in the query string (LinkedIn: `position`, `pageNum`,
        `refId`, `trackingId`; Hirist: `ref`, `jobPos`) that's different on
        every page load even for the exact same posting, while the job's
        actual identity lives in the path (which includes a stable numeric
        id for both portals). Left un-stripped, the same job scraped twice
        would get two different `source_url` values, defeating both the
        `Job.source_url` UNIQUE constraint and `create_job_records()`'s
        dedup — the same underlying posting would accumulate a fresh row
        on every scrape run instead of ever matching an existing one.
    """
    return urlsplit(url)._replace(query="", fragment="").geturl()


def parse_linkedin_jobs(soup):
    """Parse LinkedIn's public job-search results page.

    Input: soup (BeautifulSoup) — parsed HTML of a `linkedin.com/jobs/search` results page.
    Output: list[dict] — one dict per listing: title, company, location,
        source ("LinkedIn"), source_url.

    Calls: BeautifulSoup's `select()`/`select_one()` only.
    Called by: `app.services.ingestion.job_fetcher.fetch_jobs_for_designation()`.

    Variables:
        jobs (list[dict]): accumulator returned at the end.
        template (list[Tag]): one `<li>` per job card, selected via a
            fixed CSS path into LinkedIn's results markup.
        data (Tag): the card's second `<div>`, which holds title/company/location.

    Logic: for each card in `template`, pull the h3/h4/span text as
        title/company/location (each defaulting to "N/A" if missing) and
        the first `<a href>`, stripped of its volatile tracking query
        string via `_strip_tracking_params()`, as `source_url`; append the
        resulting dict.
    """
    jobs = []
    template = soup.select("body  main > section:nth-of-type(2) > ul > li")
    for job in template:
        data = job.select("div:nth-of-type(2)")[0]
        title = data.select_one("h3").text.strip() if data.select_one("h3") else "N/A"
        company = data.select_one("h4").text.strip() if data.select_one("h4") else "N/A"
        location = (
            data.select_one("span").text.strip() if data.select_one("span") else "N/A"
        )
        source_url = _strip_tracking_params(job.select("a")[0]["href"])
        logger.debug("Title: %s, Company: %s, Location: %s", title, company, location)
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source": "LinkedIn",
                "source_url": source_url,
            }
        )
    return jobs


def parse_indeed_jobs(soup):
    """Parse Indeed's job-search results page.

    Input: soup (BeautifulSoup) — parsed HTML of an `in.indeed.com/jobs` results page.
    Output: list[dict] — one dict per listing: title, company, location,
        source ("Indeed"), source_url.

    Calls: BeautifulSoup's `select()`/`select_one()` only.
    Called by: `app.services.ingestion.job_fetcher.fetch_jobs_for_designation()`.

    Variables:
        jobs (list[dict]): accumulator returned at the end.
        template (list[Tag]): every `<td>` on the page — Indeed's results
            grid puts one job card per table cell.
        anchors (list[Tag]): `<a>` tags inside the current `<td>`; a `<td>`
            with none, or whose first anchor has no `href`, is skipped
            (it's a non-job cell, e.g. a filter/pagination control).

    Logic: for each `<td>` with a usable first `<a>`, take its text as
        `title`, look up company/location via `data-testid` attributes
        (each defaulting to "N/A" if absent), and prefix the anchor's
        `href` with the Indeed origin to form an absolute URL — then, if
        it carries a `jk` query parameter, rewrite it to the bare
        `viewjob?jk=<id>` form via `_extract_jk()` (same canonicalization
        `_ingest_indeed()` uses for manually-added jobs), so the same
        posting scraped again later still lands on the same `source_url`
        despite Indeed varying the rest of the query string per request.
    """
    jobs = []
    template = soup.select("td")
    for job in template:
        anchors = job.select("a")
        if not anchors or not anchors[0].get("href"):
            continue
        title = anchors[0].text.strip() or "N/A"
        company = (
            job.select_one('[data-testid="company-name"]').text.strip()
            if job.select_one('[data-testid="company-name"]')
            else "N/A"
        )
        location = (
            job.select_one('[data-testid="text-location"]').text.strip()
            if job.select_one('[data-testid="text-location"]')
            else "N/A"
        )
        source_url = "https://in.indeed.com" + anchors[0]["href"]
        jk = _extract_jk(source_url)
        if jk:
            source_url = f"https://in.indeed.com/viewjob?jk={jk}"
        logger.debug(
            "Title: %s, Company: %s, Location: %s, Source: Indeed", title, company, location
        )
        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source": "Indeed",
                "source_url": source_url,
            }
        )
    return jobs


def parse_hirist_jobs(soup):
    """Parse Hirist's job-search results page.

    Input: soup (BeautifulSoup) — parsed HTML of a `hirist.tech/search/...`
        results page (must be pre-rendered by a browser, since Hirist is a
        React SPA — see `app.services.fetchers.playwright.fetch_page_with_browser`).
    Output: list[dict] — one dict per listing: title, company, location,
        source ("Hirist"), source_url.

    Calls: BeautifulSoup's `select()`/`select_one()`/`get_text()` only.
    Called by: `app.services.ingestion.job_fetcher.fetch_jobs_for_designation()`.

    Variables:
        jobs (list[dict]): accumulator returned at the end.
        template (list[Tag]): one `div.joblist-card-v2` per job card.
        data (str): the card's combined "Company - Title" text, split below.

    Logic: skip any card missing a title, location, or link element. For
        the rest, split the title element's text on " - " — Hirist renders
        company and title as one string with no separate DOM node for
        either — taking the part before the separator as `company` and
        after as `title` (falling back to the whole string as `title` if
        no separator is present). The link's `href` is prefixed with the
        Hirist origin and run through `_strip_tracking_params()` to drop
        its `ref`/`jobPos` query noise before becoming `source_url`.
    """
    jobs = []
    template = soup.select("div.joblist-card-v2")
    for job in template:
        title = job.select_one('[data-testid="job_title"]')
        location = job.select_one('[data-testid="job_location"]')
        link_el = job.select_one("a[href]")
        if not (title and location and link_el):
            continue
        data = title.get_text(strip=True)
        title = data.split(" - ")[1] if " - " in data else data
        company = data.split(" - ")[0]
        location = location.get_text(strip=True)
        job_url = _strip_tracking_params("https://www.hirist.tech" + link_el["href"])
        logger.debug(
            "Title: %s, Company: %s, Location: %s, Source: Hirist", title, company, location
        )

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "source_url": job_url,
                "source": "Hirist",
            }
        )
    return jobs
