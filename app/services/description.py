"""Fetch full job description from the source page."""

import requests
from bs4 import BeautifulSoup

from app.services.fetchers.page_fetcher import fetch_page_cffi
from app.services.fetchers.playwright import fetch_page_with_browser

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
_TIMEOUT = 15


def fetch_job_description(source: str, source_url: str) -> str:
    """Return the job description text for a given job page, or empty string on failure."""
    source = source.lower()

    if source == "hirist":
        # Hirist is a React app — needs a real browser to render content.
        try:
            html = fetch_page_with_browser(source_url)
        except Exception as e:
            print(f"[description] browser fetch failed for {source_url}: {e}")
            return ""
        return _parse_hirist(BeautifulSoup(html, "html.parser"))

    if source == "indeed":
        # Indeed blocks plain HTTP with a 403 security check; use curl_cffi.
        try:
            html = fetch_page_cffi(source_url, timeout=_TIMEOUT)
        except Exception as e:
            print(f"[description] cffi fetch failed for {source_url}: {e}")
            return ""
        return _parse_indeed(BeautifulSoup(html, "html.parser"))

    if source == "linkedin":
        # LinkedIn: best-effort plain HTTP (often blocked anyway).
        try:
            resp = requests.get(source_url, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"[description] fetch failed for {source_url}: {e}")
            return ""
        return _parse_linkedin(BeautifulSoup(resp.text, "html.parser"))

    return ""


def _parse_indeed(soup: BeautifulSoup) -> str:
    el = soup.select_one("#jobDescriptionText")
    return el.get_text(separator="\n", strip=True) if el else ""


def _parse_hirist(soup: BeautifulSoup) -> str:
    el = soup.select_one("div.details-container")
    return el.get_text(separator="\n", strip=True) if el else ""


def _parse_linkedin(soup: BeautifulSoup) -> str:
    # LinkedIn aggressively blocks unauthenticated requests; best-effort only.
    for selector in [
        "div.description__text",
        "section.description div",
        "div.show-more-less-html__markup",
    ]:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator="\n", strip=True)
    return ""
