
import re

from pathlib import Path
from playwright.sync_api import sync_playwright

from locator_resolver import resolve_locator


def main():
    html_file = Path(__file__).with_name("saved_test_page.html")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.goto(html_file.resolve().as_uri())

            locator, result = resolve_locator(
                page,
                label=re.compile(r"pincode|postal code", re.I),
            )

            print("Success:", result["success"])
            print("Winning strategy:", result["winning_strategy"])
            print("Attempts:", result["attempts"])

            assert result["success"] is True
            assert result["winning_strategy"] == "label"
            assert locator.count() == 1
            assert locator.evaluate("(element) => element.tagName") == "INPUT"

            print("\nRegex label resolver test passed!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
