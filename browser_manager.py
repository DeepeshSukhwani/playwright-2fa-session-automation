
"""Launch Chromium and reuse authenticated GitHub sessions."""

import logging

from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from auth import login
from config import SESSION_FILE
from session_manager import (
    is_github_session_authenticated,
    is_session_state_valid,
    save_session_state,
    clear_session_state,
)

logger = logging.getLogger("github_automation")


def create_browser_context(
        playwright: Playwright,
) -> tuple[Browser, BrowserContext, Page, bool]:
    """Create a browser and return whether its session is authenticated."""
    browser = playwright.chromium.launch(headless=False)

    if is_session_state_valid():
        context = browser.new_context(storage_state=str(SESSION_FILE))
        logger.info("Loaded saved browser session")
    else:
        context = browser.new_context()
        logger.info("No valid saved session found")

    page = context.new_page()

    try:
        authenticated = is_github_session_authenticated(page)

        if not authenticated:
            # A structurally valid state may still be expired.
            clear_session_state()
            logger.info("Saved session is not authenticated; starting login")

            stage = login(page)
            if stage != "authenticated":
                raise RuntimeError(
                    f"GitHub login did not complete; stage={stage}"
                )

            save_session_state(context)
            logger.info("Authenticated browser session saved")

        return browser, context, page, True

    except Exception:
        context.close()
        browser.close()
        raise
