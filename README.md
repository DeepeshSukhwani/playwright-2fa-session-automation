# Playwright 2FA & Session Automation

A Python automation project built with Playwright to demonstrate two-factor authentication (2FA), reusable browser sessions, multi-page navigation, dependent form handling, document capture, locator fallback strategies, retry handling, and failure evidence.

**Repository:** https://github.com/DeepeshSukhwani/playwright-2fa-session-automation

## Features

- **Automated GitHub 2FA:** Generates time-based one-time passwords (TOTP) using `pyotp`.
- **Session persistence:** Saves and reuses authenticated browser state to avoid repeating login when the session remains valid.
- **Session validation:** Detects invalid or expired sessions and initiates authentication when required.
- **Multi-page navigation:** Navigates through multiple pages and verifies the expected page state.
- **Dependent form handling:** Reads configurable input data, fills a postal code, and verifies the dependent city and state fields.
- **Document capture:** Captures an existing Amazon order invoice as a PDF.
- **Locator resolution:** Tries multiple locator strategies and records the strategy that succeeds.
- **Retry handling:** Uses bounded retries for supported retryable operations.
- **Failure evidence:** Records diagnostic information for failures, including screenshots and HTML where supported.
- **JSON manifest:** Records workflow inputs, pages visited, execution timings, captured file paths, and execution status.
- **Configurable inputs:** Uses `input.json` so supported workflow inputs can be changed without modifying the Python code.

## Technology Stack

- Python
- Playwright for Python
- `pyotp` for TOTP generation
- `python-dotenv` for environment configuration
- JSON for workflow configuration and execution results

## Project Structure

```text
playwright-2fa-session-automation/
├── auth.py
├── browser_manager.py
├── config.py
├── failure_evidence.py
├── input.json
├── locator_resolver.py
├── logging_config.py
├── retry_utils.py
├── session_manager.py
├── totp_helper.py
├── saved_test_page.html
├── amazon_workflow.py
├── test_auth_flow.py
├── test_session_reuse_flow.py
├── test_auth_totp_retry.py
├── test_browser_manager.py
├── test_failure_evidence.py
├── test_locator_failure_evidence.py
├── test_locator_resolver.py
├── test_retry_utils.py
├── test_session_manager.py
├── test_totp_helper.py
├── test_totp_retry.py
├── requirements.txt
├── .gitignore
└── README.md
```

Runtime folders such as `.auth/`, `artifacts/`, and `downloads/` are generated locally and should not be committed.

## Prerequisites

- Python 3.11 or later
- Git
- A Chromium-compatible browser installed by Playwright
- A GitHub account with TOTP-based two-factor authentication configured for the GitHub authentication workflow
- An Amazon.in account with access to an existing order invoice for the Amazon workflow

Use only accounts and data that you are authorized to access.

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/DeepeshSukhwani/playwright-2fa-session-automation.git
cd playwright-2fa-session-automation
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation, use Command Prompt instead:

```bat
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install the Playwright browser

```powershell
python -m playwright install chromium
```

If your environment restricts browser installation, use an approved installed browser or follow your organization's application-control policy.

## Environment Configuration

Create a file named `.env` in the project root for the GitHub authentication workflow. Use your own GitHub credentials and TOTP secret.

```dotenv
GITHUB_USERNAME=your_github_username
GITHUB_PASSWORD=your_github_password
GITHUB_TOTP_SECRET=your_base32_totp_secret
```

Replace the placeholder values locally. Do not commit `.env`, actual passwords, TOTP secrets, authentication cookies, or browser storage-state files.

The TOTP secret must be the secret associated with your own GitHub authenticator configuration. Do not use an OTP copied from another account.

## Workflow 1: GitHub 2FA and Session Reuse

The GitHub workflow demonstrates automated TOTP generation, authentication verification, browser-state persistence, and reuse of a saved session.

### Run the authentication flow

```powershell
python .\test_auth_flow.py
```

This test exercises the GitHub authentication flow and verifies that authentication succeeds.

### Run the session-reuse flow

```powershell
python .\test_session_reuse_flow.py
```

The session-reuse test verifies the following behavior:

1. A fresh browser context authenticates when no valid saved session is available.
2. The authenticated browser state is saved locally.
3. A subsequent browser context loads the saved state.
4. The session is checked before proceeding.
5. When the session is still valid, the workflow reuses it instead of repeating 2FA.

Session reuse is conditional. GitHub can expire or revoke a session, and a saved browser state is not a permanent authentication token.

**Note:** The Amazon workflow is separate from this GitHub TOTP workflow. Amazon sign-in and any requested OTP are handled interactively by the user.

## Workflow 2: Amazon Form Handling and Invoice Capture

The Amazon workflow demonstrates authenticated multi-page navigation, PIN-dependent address fields, and PDF document capture.

Run:

```powershell
python .\amazon_workflow.py
```

### What it does

1. Opens Amazon.in and checks the Your Orders page.
2. Reuses the saved Amazon browser state when available.
3. Waits for the user to sign in and complete any required OTP if the session is not authenticated.
4. Saves browser state after the Orders page has been verified.
5. Opens the address form and enters the configured PIN code.
6. Checks whether the dependent city and state fields are populated.
7. Captures an existing order invoice as a PDF when enabled.
8. Writes a JSON manifest with execution status and diagnostic details.

The address workflow **does not save or submit the address**. It inspects the dependent fields only.

The Amazon workflow may require interactive sign-in. It does not claim to automate Amazon's OTP delivery or generate Amazon OTPs.

### Configure the inputs

Edit `input.json` to change the supported workflow inputs. For example, the address-check section may use this structure:

```json
{
  "capture_invoice": true,
  "address_check": {
    "country": "India",
    "pin_code": "302001"
  },
  "output_directory": "downloads"
}
```

Keep the fields and structure expected by the existing `input.json` and `amazon_workflow.py` implementation. If your current file contains additional settings, preserve them.

Use a PIN code appropriate for your test. The resulting city and state depend on the portal's current behavior and the supplied PIN code.

### Generated output

The workflow generates local files, including:

```text
.auth/amazon_state.json
artifacts/manifest.json
downloads/order_invoice.pdf
```

- `.auth/amazon_state.json` stores browser authentication state.
- `artifacts/manifest.json` records workflow inputs, pages visited, timings, captured-file paths, and status.
- `downloads/order_invoice.pdf` contains the captured invoice when invoice capture succeeds.

These files are runtime artifacts, not source files for the public repository. An invoice can contain personal information, so do not publish a real invoice or its identifying details.

## Locator Resolution

The locator resolver is designed to try multiple ways to identify page elements rather than depending on a single brittle selector.

The intended fallback order prioritizes user-facing locators, such as accessible roles and names, before alternatives such as labels, nearby text, structural relationships, and IDs or classes.

The resolver logs the strategy used when it finds a matching element. This helps diagnose page changes and understand why a locator succeeded.

The repository includes `saved_test_page.html` for testing locator behavior against saved HTML without depending on a live website.

Run:

```powershell
python .\test_locator_resolver.py
```

The saved HTML test is intended to make locator behavior repeatable and easier to debug.

## Retry Handling and Failure Evidence

The project includes retry utilities and failure-evidence helpers.

The implementation supports bounded retries for operations classified as retryable. It should not retry terminal failures indefinitely or repeat sensitive actions blindly.

Relevant test commands include:

```powershell
python .\test_retry_utils.py
python .\test_auth_totp_retry.py
python .\test_totp_retry.py
python .\test_failure_evidence.py
python .\test_locator_failure_evidence.py
```

When a supported workflow fails, diagnostic evidence may include:

- A screenshot of the failed page
- Saved HTML for inspection
- The current page URL
- The failed stage or operation
- Locator-resolution attempts
- Error and timing information

Evidence is stored locally under the artifacts directory where supported. Review evidence before sharing it, since screenshots and HTML can contain account details or other sensitive data.

## Run the Supporting Tests

Run the standalone test scripts individually from the project root:

```powershell
python .\test_totp_helper.py
python .\test_totp_retry.py
python .\test_auth_totp_retry.py
python .\test_session_manager.py
python .\test_browser_manager.py
python .\test_locator_resolver.py
python .\test_failure_evidence.py
python .\test_locator_failure_evidence.py
python .\test_retry_utils.py
```

The GitHub end-to-end tests use live authentication and require a correctly configured account and `.env` file:

```powershell
python .\test_auth_flow.py
python .\test_session_reuse_flow.py
```

The Amazon workflow requires access to an Amazon account and an existing order invoice. Run it only when you are authorized to access that account.

## Security Considerations

- Never commit `.env`, passwords, TOTP secrets, browser cookies, or storage-state files.
- Do not commit `.auth/`, real invoices, screenshots containing personal data, or failure evidence containing sensitive information.
- Keep generated artifacts local and inspect them before sharing.
- Use test accounts and non-sensitive test data whenever possible.
- Do not bypass account security controls or attempt to access accounts without authorization.
- Re-authenticate through the normal sign-in process when a saved session is invalid or expired.

The `.gitignore` file excludes common local environment and runtime artifact paths. Review it before committing changes.

## Known Limitations

- GitHub authentication depends on valid credentials, a correctly configured TOTP secret, and the current login flow.
- Saved browser sessions can expire, be revoked, or require additional verification.
- Amazon OTP handling is interactive and depends on the user completing sign-in within the configured wait period.
- Amazon's page layout and invoice controls can change, which may require locator updates.
- Dependent address-field behavior can vary with the supplied PIN code and portal responses.
- Live workflows require network connectivity and valid account access.
- A successful local test does not guarantee that every future live run will succeed.

## Assignment Coverage

| Requirement | Implementation |
|---|---|
| 2FA authentication | GitHub TOTP authentication flow |
| Code generation and retry behavior | TOTP helper and authentication retry tests |
| Session persistence and reuse | Browser/session manager and session-reuse test |
| Stale-session handling | Session validation and authentication fallback |
| Multi-page navigation | GitHub and Amazon workflows |
| Dependent form fields | Amazon PIN-dependent city/state inspection |
| Document capture | Existing Amazon order invoice PDF |
| Locator fallback | Locator resolver and saved HTML test |
| Retry behavior | Retry utilities and retry tests |
| Failure diagnostics | Failure-evidence helpers and tests |
| JSON-configurable inputs | `input.json` |
| Execution manifest | `artifacts/manifest.json` |

## Author

GitHub: [DeepeshSukhwani](https://github.com/DeepeshSukhwani)

Project: [playwright-2fa-session-automation](https://github.com/DeepeshSukhwani/playwright-2fa-session-automation)
