
"""Verify that Playwright can save and reload browser state."""

from playwright.sync_api import sync_playwright

from config import SESSION_FILE
from session_manager import (
    is_session_state_valid,
    save_session_state,
)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        # Use a temporary browser context without any real credentials.
        context = browser.new_context()
        context.add_cookies([
            {
                "name": "test_cookie",
                "value": "synthetic_value",
                "url": "https://example.com",
            }
        ])

        save_session_state(context)
        assert is_session_state_valid()

        # Load the saved state into a fresh context.
        restored_context = browser.new_context(
            storage_state=str(SESSION_FILE)
        )
        cookies = restored_context.cookies("https://example.com")

        assert any(
            cookie["name"] == "test_cookie"
            and cookie["value"] == "synthetic_value"
            for cookie in cookies
        )

        restored_context.close()
        context.close()
        browser.close()

    SESSION_FILE.unlink(missing_ok=True)
    print("Session save and restore test passed")


if __name__ == "__main__":
    main()
