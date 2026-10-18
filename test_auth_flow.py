
"""Manually inspect GitHub authentication in visible Chromium."""

from playwright.sync_api import sync_playwright

from auth import login
from logging_config import configure_logging


def main() -> None:
    configure_logging()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            stage = login(page)
            print(f"Detected authentication stage: {stage}")
            print(f"Current URL: {page.url}")

        except Exception as exc:
            print(f"Login flow stopped: {type(exc).__name__}: {exc}")
            print(f"Current URL: {page.url}")

        finally:
            input(
                "Inspect the Chromium window, then press Enter here to close it..."
            )
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
