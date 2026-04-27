import requests


def fetch_page(url: str, headers: dict | None = None, timeout: int = 10) -> str:
    """
    Fetch raw HTML for a given URL.
    No parsing. No source-specific logic.
    """
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_page_cffi(url: str, timeout: int = 15) -> str:
    """
    Fetch HTML impersonating Chrome's TLS fingerprint via curl_cffi.
    Bypasses Cloudflare bot detection (used for Indeed).
    """
    from curl_cffi import requests as cffi_requests

    response = cffi_requests.get(url, impersonate="chrome124", timeout=timeout)
    response.raise_for_status()
    return response.text
