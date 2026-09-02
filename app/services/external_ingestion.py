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
    """Classify a URL's hostname against the three natively-supported portals.

    Input: url (str). Output: str | None — one of "indeed"/"linkedin"/
        "hirist", or None if no native parser matches (LLM fallback applies).
    Calls: none. Called by: `ingest_job_from_url()` (this file).
    Logic: substring-match the URL's netloc against each portal's domain,
        first match wins.
    """
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
    """Fetch and parse a single job page, dispatching by portal.

    Input:
        url (str): the job posting URL pasted by the user.
        provider (str): LLM provider to use if no native parser matches.
        api_key (str | None): caller-supplied key for that provider.

    Output: dict — title, company, location, description, source, source_url.
    Raises: ValueError/RuntimeError propagated from whichever ingest
        function is dispatched to, on fetch/parse/JSON failure.

    Calls: `detect_source()`, then one of `_ingest_indeed()` /
        `_ingest_linkedin()` / `_ingest_hirist()` / `_ingest_via_llm()`.
    Called by: `app.api.v1.job.add_job_manually()` — `POST /jobs/add`.

    Logic: classify the URL via `detect_source()`; route to the matching
        native parser, or to the LLM-extraction fallback if none match.
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
    """Pull Indeed's `jk` job-id query parameter out of a URL, if present.

    Input: url (str). Output: str | None.
    Calls: none. Called by: `_ingest_indeed()` (this file),
        `app.api.v1.job.add_job_manually()` (for pre-insert dedup).
    """
    m = re.search(r"[?&]jk=([a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def _ingest_indeed(url: str) -> dict:
    """Fetch and parse a single Indeed job-detail page.

    Input: url (str) — any Indeed job URL containing a `jk` query parameter.
    Output: dict — title, company, location, description, source ("Indeed"),
        source_url. Falls through to `_ingest_via_llm()`'s return shape if
        no title could be found natively.

    Calls: `_extract_jk()`, `fetch_page_cffi()`, BeautifulSoup parsing
        helpers, `_ingest_via_llm()` (fallback only).
    Called by: `ingest_job_from_url()` (this file).

    Variables:
        canonical_url (str): the `viewjob?jk=<id>` form of `url`, so the
            same posting reached via different query strings still
            deduplicates by `source_url` in the caller.
        title_el/company_el/location_el/desc_el: first matching element
            from an ordered list of CSS selectors, each a fallback chain
            for when Indeed's markup varies between page variants.

    Logic:
        1. Normalise to `canonical_url` via the extracted `jk`.
        2. Fetch the page HTML with `fetch_page_cffi` (TLS-fingerprint
           bypass — plain `requests` gets a 403 from Indeed).
        3. Try several CSS selectors per field, in order, keeping the
           first that matches (defends against Indeed serving slightly
           different markup across sessions/experiments).
        4. If no title was found at all, treat this as a native-parse
           failure and fall back to `_ingest_via_llm()` instead of
           returning an empty-titled result.
    """
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
    """Fetch and parse a single LinkedIn job-detail page via a real browser.

    Input: url (str) — a `linkedin.com/jobs/view/...` URL.
    Output: dict — title, company, location, description, source
        ("LinkedIn"), source_url. Fields default to "" if LinkedIn's auth
        wall blocks the expected content (no LLM fallback for this portal).

    Calls: `fetch_page_with_browser()`, BeautifulSoup parsing helpers.
    Called by: `ingest_job_from_url()` (this file).

    Logic: render the page with Playwright (LinkedIn blocks plain HTTP),
        then try one or two CSS selectors per field, defaulting to "" if
        none match — unlike `_ingest_indeed`, there is no LLM fallback
        here, so an auth-walled page yields an all-empty-field result
        rather than a second network round trip.
    """
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
    """Fetch and parse a single Hirist job-detail page via a real browser.

    Input: url (str) — a `hirist.tech/...` job-detail URL.
    Output: dict — title, company, location, description, source ("Hirist"),
        source_url.

    Calls: `fetch_page_with_browser()`, BeautifulSoup parsing helpers.
    Called by: `ingest_job_from_url()` (this file).

    Logic: render the page with Playwright (Hirist is a React SPA — plain
        HTTP would return an empty shell), then read title/company/
        location/description each from the first of two candidate
        selectors, defaulting to "" if neither matches.
    """
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
    """Fetch a page from an unsupported portal and extract job data via LLM.

    Input:
        url (str): any job posting URL not matched by `detect_source()`.
        provider (str): LLM provider to use for extraction.
        api_key (str | None): caller-supplied API key for the provider.

    Output: dict — title, company, location, description, source (derived
        from the URL's hostname, e.g. "naukri.com" -> "Naukri"), source_url.

    Raises: ValueError if the LLM response contains no parseable JSON object.

    Calls: `requests.get()` / `fetch_page_cffi()` (fallback), BeautifulSoup
        text extraction, `app.services.llm.extract_job_data()`, `json.loads()`.
    Called by: `ingest_job_from_url()` (this file), as the catch-all path
        for any URL that isn't Indeed/LinkedIn/Hirist.

    Variables:
        html (str): raw page HTML, from plain `requests` or, on failure, `fetch_page_cffi`.
        raw_text (str): the page's visible text with script/style/nav/
            footer/header tags stripped first.
        page_text (str): `raw_text` with blank lines removed and truncated
            to 8000 characters, to stay within the LLM's context budget.
        llm_response (str): the model's raw reply, expected to contain one JSON object.
        json_match: the first `{...}` substring found in `llm_response` via regex.
        data (dict): the parsed JSON object from `json_match`.
        source_name (str): the URL's hostname (stripped of "www.") with
            the TLD dropped and capitalised, used as the `source` value.

    Logic:
        1. Fetch the page: try plain `requests.get` first; if that raises,
           retry with `fetch_page_cffi` (some sites block default `requests`
           headers/TLS fingerprints but not curl-impersonation).
        2. Strip non-content tags and collapse the remaining text to
           `page_text`, capped at 8000 characters.
        3. Ask the LLM to extract structured fields from `page_text`.
        4. Regex out the first `{...}` block from the response and
           `json.loads()` it; raise ValueError if none is found.
        5. Derive `source_name` from the URL's hostname and return the
           combined result dict.
    """
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
