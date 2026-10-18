
"""Amazon workflow: validate session, inspect dependent fields, capture invoice."""

import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from config import BASE_DIR, prepare_directories
from failure_evidence import capture_failure_evidence
from logging_config import configure_logging
from locator_resolver import resolve_locator

ORDERS_URL = "https://www.amazon.in/gp/your-account/order-history"
ADDRESSES_URL = "https://www.amazon.in/a/addresses"
AUTH_FILE = BASE_DIR / ".auth" / "amazon_state.json"
INPUT_FILE = BASE_DIR / "input.json"
MANIFEST_FILE = BASE_DIR / "artifacts" / "manifest.json"

TIMEOUT_MS = 20_000
LOGIN_WAIT_MS = 120_000
DEPENDENT_FIELD_TIMEOUT_MS = 15_000

logger = logging.getLogger("github_automation")


def read_inputs() -> dict:
    """Read workflow inputs from JSON."""
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_sign_in_page(page) -> bool:
    """Detect Amazon sign-in and account-verification pages."""
    path = urlsplit(page.url).path.lower()
    return path.startswith("/ap/signin") or path.startswith("/ap/cvf/")


def is_orders_page(page) -> bool:
    """Verify the Orders page using visible content."""
    if is_sign_in_page(page):
        return False

    try:
        page.get_by_role(
            "heading", name=re.compile(r"Your Orders", re.I)
        ).wait_for(state="visible", timeout=3_000)
        return True
    except PlaywrightTimeoutError:
        return False


def ensure_session(context, page) -> None:
    """Validate the Amazon session and wait for manual login if required."""
    page.goto(
        ORDERS_URL,
        wait_until="domcontentloaded",
        timeout=TIMEOUT_MS,
    )

    if not is_orders_page(page):
        if is_sign_in_page(page):
            print("Amazon requires sign-in.")
            print("Complete login and OTP in the opened Chromium window.")
            print("Waiting up to 2 minutes...")

            try:
                page.get_by_role(
                    "heading",
                    name=re.compile(r"Your Orders", re.I),
                ).wait_for(
                    state="visible",
                    timeout=LOGIN_WAIT_MS,
                )
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(
                    "Login was not completed within 2 minutes."
                ) from exc
        else:
            raise RuntimeError(
                "Amazon opened an unexpected page; "
                "session status could not be verified."
            )

    if not is_orders_page(page):
        raise RuntimeError(
            "Amazon Orders page could not be verified after login."
        )

    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(AUTH_FILE))
    logger.info("Verified Amazon session saved")
    print("Amazon session saved successfully.")


def read_field_value(field) -> str:
    """Read an input value or selected dropdown option."""
    tag = field.evaluate("(element) => element.tagName")

    if tag == "SELECT":
        return (
                field.locator("option:checked").text_content() or ""
        ).strip()

    return (field.input_value() or "").strip()


def inspect_address_form(

        page,
        inputs: dict,
        manifest: dict,
        resolver_attempts: list,
) -> None:
    """Inspect PIN-dependent fields without saving an address."""
    page.goto(
        ADDRESSES_URL,
        wait_until="domcontentloaded",
        timeout=TIMEOUT_MS,
    )
    manifest["pages_visited"].append("Your Addresses")

    if is_sign_in_page(page):
        raise RuntimeError("Amazon session expired on Your Addresses.")

    page.get_by_text("Add address", exact=True).first.click(
        timeout=TIMEOUT_MS
    )

    address_inputs = inputs.get("address_check", {})
    pin_code = str(address_inputs.get("pin_code", "")).strip()

    if not pin_code:
        raise ValueError("address_check.pin_code is missing from input.json")

    pin_field, pin_result = resolve_locator(
        page,
        label=re.compile(r"pincode|postal code", re.I),
    )

    resolver_attempts.extend(pin_result["attempts"])

    if not pin_result["success"] or pin_field is None:
        raise RuntimeError(
            "Could not uniquely locate the PIN code field."
        )

    pin_field.wait_for(state="visible", timeout=TIMEOUT_MS)
    pin_field.fill(pin_code)
    pin_field.press("Tab")

    city_field = page.get_by_label(
        re.compile(r"Town/City|City", re.I)
    ).first
    state_field = page.get_by_label(
        re.compile(r"State", re.I)
    ).first

    try:
        page.wait_for_function(
            """() => {
                const visible = el => el && el.getClientRects().length > 0;
                const labelOf = el =>
                    (el.labels?.[0]?.innerText || '') + ' ' +
                    (el.getAttribute('aria-label') || '') + ' ' +
                    (el.name || '');

                const city = [...document.querySelectorAll('input')]
                    .find(el => visible(el) &&
                        /town\\/city|city/i.test(labelOf(el)));

                const state = [
                    ...document.querySelectorAll('select, input')
                ].find(el => visible(el) && /state/i.test(labelOf(el)));

                if (!city || !state) return false;

                const value = state.tagName === 'SELECT'
                    ? state.options[state.selectedIndex]?.text
                    : state.value;

                return Boolean(city.value?.trim()) &&
                    Boolean(value?.trim()) &&
                    !/choose|select/i.test(value);
            }""",
            timeout=DEPENDENT_FIELD_TIMEOUT_MS,
        )
    except PlaywrightTimeoutError:
        logger.warning("PIN-dependent fields did not populate in time")

    fields = {}
    if city_field.count():
        fields["Town/City"] = read_field_value(city_field)
    if state_field.count():
        fields["State"] = read_field_value(state_field)

    populated = bool(
        fields.get("Town/City")
        and fields.get("State")
        and not re.search(
            r"choose|select", fields.get("State", ""), re.I
        )
    )

    manifest["address_check"] = {
        "country": address_inputs.get("country"),
        "pin_code": pin_code,
        "location_fields": fields,
        "dependent_fields_populated": populated,
        "address_saved": False,
    }

    print(f"Location fields: {fields}")
    print(f"Dependent fields populated: {populated}")
    print("Address was not saved.")

    if not populated:
        logger.warning("PIN-dependent field validation failed")


def capture_invoice(page, context, inputs: dict, manifest: dict) -> None:
    """Open an invoice and save its PDF bytes."""
    page.goto(
        ORDERS_URL,
        wait_until="domcontentloaded",
        timeout=TIMEOUT_MS,
    )

    if not is_orders_page(page):
        raise RuntimeError("Amazon Orders page could not be verified.")

    manifest["pages_visited"].append("Your Orders")

    invoice_links = page.get_by_role(
        "link", name="Invoice", exact=True
    )
    count = invoice_links.count()
    print("Invoice controls found:", count)

    if count == 0:
        raise RuntimeError("No Invoice controls were found on Your Orders.")

    invoice_link = invoice_links.first
    invoice_link.wait_for(state="visible", timeout=TIMEOUT_MS)
    invoice_link.click(timeout=TIMEOUT_MS)

    candidates = page.get_by_role(
        "link", name=re.compile(r"^Invoice$", re.I)
    )
    candidate_count = candidates.count()
    print("Exact Invoice links after opening menu:", candidate_count)

    selected_link = None
    for index in range(candidate_count):
        candidate = candidates.nth(index)
        href = candidate.get_attribute("href") or ""
        if re.search(r"invoice|documents/download", href, re.I):
            selected_link = candidate
            break

    if selected_link is None:
        selected_link = invoice_link

    started = time.perf_counter()
    invoice_page = None

    try:
        try:
            with context.expect_page(timeout=5_000) as new_page:
                selected_link.click(timeout=TIMEOUT_MS)
            invoice_page = new_page.value
        except PlaywrightTimeoutError:
            logger.info("No new tab detected; checking current page")
            invoice_page = page

        document_url_pattern = re.compile(
            r"/documents/download/|invoice\.pdf",
            re.I,
        )

        if invoice_page is page:
            try:
                page.wait_for_url(
                    document_url_pattern,
                    timeout=TIMEOUT_MS,
                )
            except PlaywrightTimeoutError as exc:
                raise RuntimeError(
                    "Invoice click did not navigate to a document URL."
                ) from exc
        else:
            invoice_page.wait_for_url(
                document_url_pattern,
                timeout=TIMEOUT_MS,
            )

        response = context.request.get(
            invoice_page.url,
            timeout=TIMEOUT_MS,
        )

        if not response.ok:
            raise RuntimeError(
                f"Invoice request failed: HTTP {response.status}"
            )

        pdf_bytes = response.body()
        if not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError("The response was not a valid PDF.")

        output_name = Path(
            inputs.get("output_directory", "downloads")
        )
        if output_name.is_absolute() or ".." in output_name.parts:
            raise ValueError("output_directory must be a safe relative path")

        output_dir = BASE_DIR / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "order_invoice.pdf"
        output_file.write_bytes(pdf_bytes)

        manifest["pages_visited"].append("Order invoice PDF")
        manifest["captured_files"].append(
            str(output_file.relative_to(BASE_DIR))
        )
        manifest["stage_timings_seconds"]["capture_invoice"] = round(
            time.perf_counter() - started, 3
        )
        print(f"Invoice saved: {output_file.relative_to(BASE_DIR)}")

    finally:
        if invoice_page is not None and invoice_page is not page:
            try:
                if not invoice_page.is_closed():
                    invoice_page.close()
            except Exception as exc:
                logger.warning(
                    "Invoice tab cleanup failed: %s",
                    type(exc).__name__,
                )


def main() -> None:
    """Run the workflow and write a manifest on success or failure."""
    configure_logging()
    prepare_directories()
    inputs = read_inputs()

    manifest = {
        "portal": "Amazon.in",
        "inputs": {
            "capture_invoice": bool(
                inputs.get("capture_invoice", False)
            ),
            "address_country": inputs.get(
                "address_check", {}
            ).get("country"),
            "address_pin_code": inputs.get(
                "address_check", {}
            ).get("pin_code"),
        },
        "pages_visited": [],
        "stage_timings_seconds": {},
        "captured_files": [],
        "status": "running",
    }

    started = time.perf_counter()
    browser = None
    context = None
    page = None
    current_stage = "browser_setup"
    resolver_attempts = []


    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)

            current_stage = "session_setup"
            options = {}
            if AUTH_FILE.is_file():
                options["storage_state"] = str(AUTH_FILE)

            context = browser.new_context(**options)
            page = context.new_page()

            # Collect browser console messages for failure diagnostics.
            page._failure_console_logs = []

            page.on(
                "console",
                lambda message: page._failure_console_logs.append(
                    f"{message.type}: {message.text}"
                ),
            )

            current_stage = "session_validation"
            ensure_session(context, page)
            manifest["pages_visited"].append("Your Orders")

            if inputs.get("address_check"):
                current_stage = "address_check"
                stage_start = time.perf_counter()
                inspect_address_form(
                    page, inputs, manifest, resolver_attempts
                )
                manifest["stage_timings_seconds"]["address_check"] = round(
                    time.perf_counter() - stage_start, 3
                )

            if inputs.get("capture_invoice", False):
                current_stage = "invoice_capture"
                capture_invoice(page, context, inputs, manifest)

            manifest["status"] = "success"
            print("Amazon workflow completed.")

    except Exception as exc:
        manifest["status"] = "failed"
        manifest["failure_stage"] = current_stage
        logger.error(
            "Amazon workflow failed during stage: %s",
            current_stage,
        )

        if page is not None:
            try:
                evidence = capture_failure_evidence(
                    page=page,
                    stage=current_stage,
                    error=exc,
                    resolver_attempts=resolver_attempts,
                )
                manifest["failure_evidence"] = evidence
            except Exception:
                logger.exception("Failure-evidence capture also failed")

        # Avoid logging the exception text here because it may contain
        # URLs or data that has not been sanitized.
        raise

    finally:
        if context is not None:
            try:
                context.close()
                logger.info("Browser context closed")
            except Exception as exc:
                logger.warning(
                    "Browser context cleanup failed: %s",
                    type(exc).__name__,
                )

        if browser is not None:
            try:
                if browser.is_connected():
                    browser.close()
                    logger.info("Browser closed")
                else:
                    logger.info("Browser was already disconnected")
            except Exception as exc:
                logger.warning(
                    "Browser cleanup failed: %s",
                    type(exc).__name__,
                )

        manifest["stage_timings_seconds"]["total"] = round(
            time.perf_counter() - started, 3
        )

        MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_FILE.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        print(f"Manifest written: {MANIFEST_FILE.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
