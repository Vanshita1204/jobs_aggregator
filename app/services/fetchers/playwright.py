from playwright.sync_api import sync_playwright


def fetch_page_with_browser(url: str, timeout: int = 30000) -> str:
    """
    Fetch page HTML using a real browser.
    """
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,  # important for some anti-bot systems
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()

        page.goto(url, timeout=timeout)

        # wait for page JS
        try:
            page.wait_for_load_state("networkidle")
        except:
            pass
        # scroll to trigger lazy loading
        for _ in range(3):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1500)
        html = page.content()
        browser.close()
        return html
