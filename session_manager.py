
"""Manage saved Playwright session state."""

import json

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from config import GITHUB_BASE_URL, SESSION_FILE


def is_session_state_valid() -> bool:
    """Check whether the saved state has a valid structure."""
    if not SESSION_FILE.is_file():
        return False

    try:
        with SESSION_FILE.open("r", encoding="utf-8") as file:
            state = json.load(file)

        return (
                isinstance(state, dict)
                and isinstance(state.get("cookies"), list)
                and isinstance(state.get("origins"), list)
        )
    except (OSError, json.JSONDecodeError):
        return False


def save_session_state(context) -> None:
    """Save browser storage state locally."""
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(SESSION_FILE))


def clear_session_state() -> None:
    """Delete saved state when it cannot be reused."""
    SESSION_FILE.unlink(missing_ok=True)


def is_github_session_authenticated(page: Page) -> bool:
    """Return whether GitHub displays the authenticated settings page."""
    page.goto(
        f"{GITHUB_BASE_URL}/settings/profile",
        wait_until="commit",
        timeout=30_000,
    )

    # A login redirect is evidence that the session isn't authenticated.
    if "/login" in page.url:
        return False

    try:
        page.get_by_role(
            "heading", name="Public profile"
        ).wait_for(state="visible", timeout=10_000)
        return True
    except PlaywrightTimeoutError:
        # A missing heading alone doesn't prove the session has expired.
        return False
