import os
from playwright.sync_api import sync_playwright

DEFAULT_HANDLE_SELECTOR = "div.yt-content-metadata-view-model-wiz__metadata-row span.yt-core-attributed-string--link-inherit-color"
HANDLE_ELEMENT = os.environ.get("HANDLE_ELEMENT", DEFAULT_HANDLE_SELECTOR)

def get_channel_handle(channel_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(channel_url, wait_until="networkidle")
            handle_elem = page.query_selector(HANDLE_ELEMENT)
            handle = handle_elem.inner_text() if handle_elem else "N/A"
        except Exception:
            handle = "N/A"
        browser.close()
        return handle