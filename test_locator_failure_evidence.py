
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from failure_evidence import capture_failure_evidence
from locator_resolver import resolve_locator


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.set_content("""
                <!DOCTYPE html>
                <html>
                  <body>
                    <h2>Test Form</h2>
                    <input id="email" type="email">
                  </body>
                </html>
            """)

            locator, result = resolve_locator(
                page,
                role="button",
                name="Continue",
                label="Missing label",
                nearby_text="Missing text",
                tag="button",
                element_id="missing-id",
                class_name="missing-class",
            )

            assert locator is None
            assert result["success"] is False

            evidence = capture_failure_evidence(
                page=page,
                stage="locator_failure_test",
                error=RuntimeError("Simulated locator failure"),
                resolver_attempts=result["attempts"],
            )

            evidence_path = (
                    Path(__file__).parent
                    / evidence["html"].replace("\\", "/")
                    .replace("artifacts/failures/", "artifacts/failures/")
            )

            json_path = Path(__file__).parent / "artifacts" / "failures"
            candidates = sorted(
                json_path.glob("*_locator_failure_test.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )

            assert candidates, "Evidence JSON was not created"

            saved = json.loads(
                candidates[0].read_text(encoding="utf-8")
            )

            assert saved["stage"] == "locator_failure_test"
            assert saved["resolver_attempts"]
            assert all(
                attempt["status"] in {
                    "no_match",
                    "multiple_matches",
                    "error",
                    "matched",
                }
                for attempt in saved["resolver_attempts"]
            )

            print("Locator success:", result["success"])
            print("Resolver attempts:", result["attempts"])
            print("Evidence JSON:", candidates[0])
            print("\nLocator failure-evidence test passed!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
