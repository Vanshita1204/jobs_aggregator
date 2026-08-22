"""Ingest a single job from an arbitrary URL.

Supported natively: Indeed, LinkedIn, Hirist.
Everything else: fetch page text → LLM extraction.
"""

import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.services.fetchers.page_fetcher import fetch_page_cffi
from app.services.fetchers.playwright import fetch_page_with_browser
from app.services.llm import extract_job_data

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def detect_source(url: str) -> str | None:
    """Return normalised source name if we have a native parser, else None."""
    host = urlparse(url).netloc.lower()
    if "indeed.com" in host:
        return "indeed"
    if "linkedin.com" in host:
        return "linkedin"
    if "hirist.tech" in host:
        return "hirist"
    return None


def ingest_job_from_url(
    url: str,
    provider: str = "groq",
    api_key: str | None = None,
) -> dict:
    """
    Fetch + parse a single job page.
    Returns dict: title, company, location, description, source, source_url.
    Raises ValueError/RuntimeError on failure.
    """
    source = detect_source(url)

    if source == "indeed":
        return _ingest_indeed(url)
    if source == "linkedin":
        return _ingest_linkedin(url)
    if source == "hirist":
        return _ingest_hirist(url)

    return _ingest_via_llm(url, provider=provider, api_key=api_key)


# ── Supported source parsers ────────────────────────────────────────────────

def _extract_jk(url: str) -> str | None:
    m = re.search(r"[?&]jk=([a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def _ingest_indeed(url: str) -> dict:
    jk = _extract_jk(url)
    canonical_url = f"https://in.indeed.com/viewjob?jk={jk}" if jk else url

    html = fetch_page_cffi(canonical_url)
    soup = BeautifulSoup(html, "html.parser")

    title_el = (
        soup.select_one("h1[data-testid='jobsearch-JobInfoHeader-title']")
        or soup.select_one("h1.jobsearch-JobInfoHeader-title")
        or soup.select_one("[data-testid='jobsearch-JobInfoHeader-title']")
        or soup.select_one("h1")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    company_el = (
        soup.select_one("[data-testid='inlineHeader-companyName']")
        or soup.select_one("[data-company-name='true']")
        or soup.select_one("[data-testid='companyName']")
        or soup.select_one(".jobsearch-CompanyInfoContainer a")
    )
    company = company_el.get_text(strip=True) if company_el else ""

    location_el = (
        soup.select_one("[data-testid='job-location']")
        or soup.select_one("[data-testid='jobsearch-JobInfoHeader-locationWrapper']")
    )
    location = location_el.get_text(strip=True) if location_el else ""

    desc_el = (
        soup.select_one("#jobDescriptionText")
        or soup.select_one(".jobsearch-jobDescriptionText")
        or soup.select_one("[data-testid='jobDescriptionText']")
    )
    description = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

    # If native selectors all missed, fall back to LLM
    if not title:
        return _ingest_via_llm(canonical_url, provider="groq", api_key=None)

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "source": "Indeed",
        "source_url": canonical_url,
    }


def _ingest_linkedin(url: str) -> dict:
    html = fetch_page_with_browser(url)
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("h1.top-card-layout__title") or soup.select_one("h1")
    title = title_el.get_text(strip=True) if title_el else ""

    company_el = (
        soup.select_one(".topcard__org-name-link")
        or soup.select_one("[data-tracking-control-name='public_jobs_topcard-org-name']")
    )
    company = company_el.get_text(strip=True) if company_el else ""

    location_el = soup.select_one(".topcard__flavor--bullet")
    location = location_el.get_text(strip=True) if location_el else ""

    desc_el = (
        soup.select_one("div.description__text")
        or soup.select_one("div.show-more-less-html__markup")
    )
    description = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "source": "LinkedIn",
        "source_url": url,
    }


def _ingest_hirist(url: str) -> dict:
    html = fetch_page_with_browser(url)
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("h1") or soup.select_one("[data-testid='job_title']")
    title = title_el.get_text(strip=True) if title_el else ""

    company_el = (
        soup.select_one("[data-testid='company_name']")
        or soup.select_one(".company-name")
    )
    company = company_el.get_text(strip=True) if company_el else ""

    location_el = (
        soup.select_one("[data-testid='job_location']")
        or soup.select_one(".job-location")
    )
    location = location_el.get_text(strip=True) if location_el else ""

    desc_el = soup.select_one("div.details-container") or soup.select_one(".job-description")
    description = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

    return {
        "title": title,
        "company": company,
        "location": location,
        "description": description,
        "source": "Hirist",
        "source_url": url,
    }


# ── LLM fallback ─────────────────────────────────────────────────────────────

def _ingest_via_llm(url: str, provider: str, api_key: str | None) -> dict:
    # Fetch page — try plain HTTP first, then cffi on failure
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        html = fetch_page_cffi(url)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    raw_text = soup.get_text(separator="\n", strip=True)
    # Trim to avoid LLM context limits
    page_text = "\n".join(line for line in raw_text.splitlines() if line.strip())[:8000]

    llm_response = extract_job_data(page_text, provider=provider, api_key=api_key)

    # Pull the first JSON object out of the response
    json_match = re.search(r"\{[^{}]*\}", llm_response, re.DOTALL)
    if not json_match:
        raise ValueError(f"LLM did not return valid JSON: {llm_response[:300]}")
    data = json.loads(json_match.group(0))

    host = urlparse(url).netloc.replace("www.", "")
    source_name = host.split(".")[0].capitalize()

    return {
        "title": data.get("title", ""),
        "company": data.get("company", ""),
        "location": data.get("location", ""),
        "description": data.get("description", ""),
        "source": source_name,
        "source_url": url,
    }
