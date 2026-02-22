from playwright.sync_api import sync_playwright


def fetch_page_with_browser(url: str, timeout: int = 30_000) -> str:
    """
    Fetch page HTML using a real browser.
    Use ONLY when normal HTTP requests fail.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout)
        html = page.content()
        browser.close()
        return html
