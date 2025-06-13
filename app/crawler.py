import os
import logging
from playwright.sync_api import sync_playwright

# ✅ Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Selector (can be overridden via env var)
DEFAULT_HANDLE_SELECTOR = "div.yt-content-metadata-view-model-wiz__metadata-row span.yt-core-attributed-string--link-inherit-color"
HANDLE_ELEMENT = os.environ.get("HANDLE_ELEMENT", DEFAULT_HANDLE_SELECTOR)

def get_channel_handle(channel_url):
    logger.info(f"Launching browser to get handle from: {channel_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            logger.info(f"Navigating to channel URL: {channel_url}")
            page.goto(channel_url, wait_until="networkidle")

            logger.info(f"Looking for handle using selector: {HANDLE_ELEMENT}")
            handle_elem = page.query_selector(HANDLE_ELEMENT)

            if handle_elem:
                handle = handle_elem.inner_text()
                logger.info(f"Extracted handle: {handle}")
            else:
                handle = "N/A"
                logger.warning("Handle element not found on page.")
        except Exception as e:
            handle = "N/A"
            logger.error(f"Error while extracting handle from {channel_url}: {e}")
        finally:
            browser.close()
            logger.info("Browser closed.")

    return handle
