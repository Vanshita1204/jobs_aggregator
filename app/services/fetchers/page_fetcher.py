from urllib.parse import urlparse

import requests

_BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def fetch_page(url: str, headers: dict | None = None, timeout: int = 10) -> str:
    """
    Fetch raw HTML for a given URL.
    No parsing. No source-specific logic.
    """
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_page_cffi(url: str, timeout: int = 20) -> str:
    """
    Fetch HTML impersonating Chrome's TLS fingerprint via curl_cffi.
    Uses a session so cookies are preserved across the homepage warm-up
    and the target request, which is required to pass Indeed's bot checks.
    """
    from curl_cffi import requests as cffi_requests

    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    session = cffi_requests.Session(impersonate="chrome131")

    # Warm up: visit the homepage first to receive anti-bot cookies
    try:
        session.get(origin, headers=_BROWSER_HEADERS, timeout=timeout)
    except Exception:
        pass  # best-effort; proceed even if homepage is unreachable

    headers = {
        **_BROWSER_HEADERS,
        "Referer": origin + "/",
        "Sec-Fetch-Site": "same-origin",
    }
    response = session.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text
