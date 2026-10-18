
import json

from playwright.sync_api import sync_playwright

from failure_evidence import capture_failure_evidence
from locator_resolver import resolve_locator


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()

            page._failure_console_logs = []
            page.on(
                "console",
                lambda message: page._failure_console_logs.append(
                    f"{message.type}: {message.text}"
                ),
            )

            page.set_content("""
                <!DOCTYPE html>
                <html>
                  <body>
                    <label for="email">Email address</label>
                    <input id="email" type="email">
                  </body>
                </html>
            """)

            page.evaluate("console.error('Dummy failure test')")

            # Simulate a locator fallback and capture its attempts.
            _, locator_result = resolve_locator(
                page,
                role="button",
                name="Continue",
                label="Email address",
            )

            print("Locator result:", locator_result)

            # Simulate a workflow failure with locator diagnostics.
            result = capture_failure_evidence(
                page=page,
                stage="locator_evidence_test",
                error=RuntimeError("Dummy test error"),
                resolver_attempts=locator_result["attempts"],
            )

            print("Captured console logs:", result["console_logs"])
            print("Captured resolver attempts:", result["resolver_attempts"])

            metadata_path = result["html"]
            evidence_json = (
                    __import__("pathlib").Path(__file__).parent
                    / "artifacts"
                    / "failures"
            )

            json_files = sorted(
                evidence_json.glob("*_locator_evidence_test.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )

            assert json_files, "Failure-evidence JSON was not created"

            saved_result = json.loads(
                json_files[0].read_text(encoding="utf-8")
            )

            assert saved_result["resolver_attempts"] == locator_result["attempts"]
            assert saved_result["console_logs"]
            assert saved_result["stage"] == "locator_evidence_test"

            print("Evidence JSON:", json_files[0])
            print("HTML evidence:", metadata_path)
            print("\nFailure-evidence integration test passed!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
