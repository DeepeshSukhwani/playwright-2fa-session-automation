
"""Test session reuse and inspect GitHub repository navigation."""

from playwright.sync_api import sync_playwright

from browser_manager import create_browser_context
from logging_config import configure_logging


PAGES_TO_VISIT = [
    ("Profile settings", "https://github.com/settings/profile"),
    ("Security settings", "https://github.com/settings/security"),
    ("Your repositories", "https://github.com/settings/repositories"),
]


def main() -> None:
    configure_logging()

    with sync_playwright() as playwright:
        browser, context, page, authenticated = create_browser_context(playwright)

        try:
            print(f"Authenticated: {authenticated}")

            if not authenticated:
                raise RuntimeError("GitHub authentication was not completed")

            for name, url in PAGES_TO_VISIT:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                print(f"\n{name}: {page.url}")
                print(f"Title: {page.title()}")

            print("\nVisible repository-related links:")

            links = page.locator("a")
            for index in range(min(links.count(), 100)):
                link = links.nth(index)

                if not link.is_visible():
                    continue

                text = (link.inner_text(timeout=2_000) or "").strip()
                href = link.get_attribute("href") or ""

                if text and (
                        "new" in text.lower()
                        or "repository" in text.lower()
                ):
                    print(f"Link: {text[:80]} | {href}")

            input("\nInspect Chromium, then press Enter to close it...")

        finally:
            context.close()
            browser.close()

    print("\nNavigation inspection completed.")


if __name__ == "__main__":
    main()
