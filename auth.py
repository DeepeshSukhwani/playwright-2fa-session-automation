
"""Handle GitHub login and two-factor authentication."""

import logging

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from config import GITHUB_LOGIN_URL, GITHUB_PASSWORD, GITHUB_USERNAME
from totp_helper import generate_totp_code

logger = logging.getLogger("github_automation")

TIMEOUT_MS = 15_000
NAVIGATION_TIMEOUT_MS = 30_000
PROFILE_URL = "https://github.com/settings/profile"
MAX_TOTP_ATTEMPTS = 2


def _has_totp_rejection(page: Page) -> bool:
    """Detect a visible error indicating that the submitted TOTP was rejected."""
    error_locators = [
        page.get_by_role("alert"),
        page.locator("#app_totp ~ .error"),
        page.locator("[data-testid*='error']"),
    ]

    rejection_phrases = (
        "invalid",
        "incorrect",
        "doesn't match",
        "did not match",
        "try again",
    )

    for locator in error_locators:
        try:
            count = min(locator.count(), 5)
            for index in range(count):
                item = locator.nth(index)
                if not item.is_visible():
                    continue

                message = item.inner_text(timeout=1_000).strip().lower()
                if message and any(
                        phrase in message for phrase in rejection_phrases
                ):
                    return True
        except PlaywrightTimeoutError:
            continue

    return False


def _verify_authenticated_session(page: Page) -> str:
    """Check access to a protected GitHub page."""
    page.goto(
        PROFILE_URL,
        wait_until="commit",
        timeout=NAVIGATION_TIMEOUT_MS,
    )

    if "/login" in page.url or "/sessions/two-factor/" in page.url:
        logger.warning("GitHub redirected to authentication")
        return "not_authenticated"

    try:
        page.get_by_role("heading", name="Public profile").wait_for(
            state="visible",
            timeout=TIMEOUT_MS,
        )
    except PlaywrightTimeoutError:
        logger.warning("Protected profile heading was not found")
        return "not_authenticated"

    logger.info("GitHub authentication verified")
    return "authenticated"


def _submit_totp(page: Page) -> str:
    """Submit TOTP and retry once only after an explicit rejection."""
    code_input = page.locator("#app_totp")
    verify_button = page.get_by_role("button", name="Verify")

    code_input.wait_for(state="visible", timeout=TIMEOUT_MS)
    verify_button.wait_for(state="visible", timeout=TIMEOUT_MS)

    for attempt in range(1, MAX_TOTP_ATTEMPTS + 1):
        code_input.fill(generate_totp_code())

        try:
            with page.expect_navigation(
                    wait_until="commit",
                    timeout=NAVIGATION_TIMEOUT_MS,
            ):
                verify_button.click(
                    timeout=TIMEOUT_MS,
                    no_wait_after=True,
                )
        except PlaywrightTimeoutError:
            # Navigation may not occur when the code is rejected.
            logger.info("No navigation event observed after TOTP submission")

        status = _verify_authenticated_session(page)
        if status == "authenticated":
            return status

        # Only retry if GitHub explicitly displays a rejection.
        if attempt < MAX_TOTP_ATTEMPTS and _has_totp_rejection(page):
            logger.warning("GitHub rejected a TOTP attempt; retrying once")
            page.go_back(
                wait_until="commit",
                timeout=NAVIGATION_TIMEOUT_MS,
            )
            code_input.wait_for(state="visible", timeout=TIMEOUT_MS)
            verify_button.wait_for(state="visible", timeout=TIMEOUT_MS)
            continue

        logger.error("GitHub TOTP authentication did not complete")
        return "not_authenticated"

    return "not_authenticated"


def login(page: Page) -> str:
    """Submit credentials and complete TOTP when requested."""
    if not GITHUB_USERNAME or not GITHUB_PASSWORD:
        raise ValueError("GitHub login credentials are not configured")

    try:
        page.goto(
            GITHUB_LOGIN_URL,
            wait_until="commit",
            timeout=NAVIGATION_TIMEOUT_MS,
        )

        page.get_by_label("Username or email address").fill(GITHUB_USERNAME)
        page.get_by_label("Password").fill(GITHUB_PASSWORD)
        page.get_by_role("button", name="Sign in").click(
            timeout=TIMEOUT_MS,
            no_wait_after=True,
        )

        page.wait_for_url(
            lambda url: (
                    "/sessions/two-factor/" in str(url)
                    or "/login" not in str(url)
            ),
            timeout=TIMEOUT_MS,
        )

        if "/sessions/two-factor/" in page.url:
            logger.info("GitHub requested two-factor authentication")
            return _submit_totp(page)

        return _verify_authenticated_session(page)

    except PlaywrightTimeoutError:
        logger.error("Timed out waiting for a GitHub page state")
        raise
    except ValueError:
        logger.error("Authentication configuration is invalid")
        raise
    except Exception:
        logger.exception("GitHub authentication failed")
        raise
