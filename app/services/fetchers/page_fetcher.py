import requests


def fetch_page(url: str, headers: dict | None = None, timeout: int = 10) -> str:
    """
    Fetch raw HTML for a given URL.
    No parsing. No source-specific logic.
    """
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text
