# Playwright 2FA and Session Automation

A Python automation project built with Playwright to demonstrate two-factor authentication, browser session reuse, multi-page navigation, dependent form handling, document capture, and execution reporting.

## Features

- GitHub authentication using automatically generated TOTP codes.
- Browser session persistence and reuse across runs.
- Authentication validation and fresh login when a saved session is invalid.
- Multi-page navigation through authenticated pages.
- Dynamic, dependent form-field inspection using a PIN code.
- PDF invoice capture from an existing Amazon order.
- JSON manifest containing inputs, visited pages, timings, captured files, and workflow status.
- Resilient locator resolution using accessible roles, labels, text, and structural fallbacks.
- Structured logging and failure evidence for troubleshooting.
- Local configuration and authentication-state files excluded from Git.

## Tech Stack

- Python
- Playwright
- Chromium
- PyOTP
- python-dotenv
- JSON

## Project Structure

```text
playwright-2fa-session-automation/
├── auth.py
├── browser_manager.py
├── config.py
├── logging_config.py
├── totp_helper.py
├── amazon_workflow.py
├── input.json
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── tests/
├── artifacts/       # Generated execution reports
├── downloads/       # Captured documents
└── .auth/           # Local browser authentication state
```

Generated files and optional diagnostic scripts may differ from this structure.

## Prerequisites

- Python 3.11 or later
- Git
- Chromium supported by Playwright
- Authorized GitHub credentials and a configured TOTP secret for the GitHub workflow
- An Amazon account with access to an existing order invoice for the Amazon workflow

## Setup

Clone the repository and enter the project directory:

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd playwright-2fa-session-automation
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies and Chromium:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

Create a local `.env` file using `.env.example` as a template:

```dotenv
GITHUB_USERNAME=your_github_username
GITHUB_PASSWORD=your_github_password
GITHUB_TOTP_SECRET=your_totp_secret
```

Use the exact environment-variable names expected by the code. Never commit real credentials, TOTP secrets, or authentication-state files.

## Workflow 1: GitHub 2FA and Session Reuse

### Verify authentication

```powershell
python .\test_auth_flow.py
```

This script exercises GitHub login, generates a TOTP code, and verifies that authentication succeeds.

### Verify session reuse

```powershell
python .\test_session_reuse_flow.py
```

On the first run, the script authenticates and saves the browser session. On a subsequent run, it loads the saved session and verifies access to the Profile, Security, and Repositories settings pages.

**Verified behavior:** the first run authenticated and saved the session. The second run reported `Loaded saved browser session` and `Authenticated: True` without repeating login or TOTP.

These commands require the corresponding scripts to be present in the repository.

## Workflow 2: Amazon Form Inspection and Invoice Capture

Run the Amazon workflow:

```powershell
python .\amazon_workflow.py
```

The workflow:

1. Opens the Amazon Orders page and checks the saved session.
2. Requests manual sign-in and OTP completion when necessary.
3. Saves the verified browser session locally.
4. Navigates to the address form and enters the configured PIN code.
5. Inspects dependent Town/City and State fields without saving the address.
6. Opens an existing order invoice and captures the PDF.
7. Writes a JSON manifest containing execution details.
8. Closes browser resources and records failure information when execution fails.

Amazon sign-in may require manual interaction. This workflow does not claim to automate Amazon OTP retrieval.

### Configure `input.json`

Example configuration:

```json
{
  "capture_invoice": true,
  "address_check": {
    "country": "India",
    "pin_code": "YOUR_TEST_PIN_CODE"
  },
  "output_directory": "downloads"
}
```

Use a valid test PIN code and an account you are authorized to access. The address inspection does not save or submit an address.

## Session Management

Browser authentication state is stored locally for reuse.

- Missing or invalid session state triggers authentication.
- Valid saved state allows authenticated navigation without repeating login.
- Expired sessions must be detected before protected workflow steps continue.
- Authentication-state files are excluded from version control.

## Locator Resolution

The locator resolver prioritizes resilient selectors in this order:

1. Accessible role and name.
2. Associated label.
3. Nearby or descriptive text.
4. Structural relationships.
5. Stable IDs or classes as fallbacks.

The successful strategy is logged to make locator decisions easier to inspect and troubleshoot.

## Reliability and Failure Evidence

The workflow uses bounded waits, structured logging, and error handling to improve reliability.

When configured, failure evidence can include:

- Failed workflow stage.
- Current page URL.
- Screenshot and HTML snapshot.
- Locator-resolution attempts.
- Error details and execution timings.
- JSON manifest.

Review failure evidence for sensitive information before sharing it.

## Output Artifacts

| Artifact | Purpose |
|---|---|
| `artifacts/manifest.json` | Inputs, pages visited, timings, status, and captured-file paths |
| `downloads/order_invoice.pdf` | Captured invoice from an existing order |
| Failure evidence | Troubleshooting information for unsuccessful runs |
| Local browser state | Authenticated session reuse |

These files are generated at runtime. Do not commit invoices, account information, browser state, or sensitive failure evidence.

## Validation

Run the GitHub workflow checks:

```powershell
python .\test_auth_flow.py
python .\test_session_reuse_flow.py
```

Run the Amazon workflow:

```powershell
python .\amazon_workflow.py
```

Check Python syntax:

```powershell
python -m py_compile .\amazon_workflow.py
```

The GitHub session-reuse check should confirm that the saved session loads successfully. A successful Amazon run should produce a success manifest and capture the invoice when invoice capture is enabled.

## Security

- Keep `.env` out of Git.
- Keep `.auth/` and browser storage-state files out of Git.
- Do not commit invoices or screenshots containing personal information.
- Never log passwords, TOTP secrets, or authentication codes.
- Use only accounts and documents you are authorized to access.

## Limitations

- Website layouts and authentication behavior may change.
- Saved sessions may expire or be invalidated.
- Amazon login may require manual interaction.
- Invoice capture requires an accessible existing order and invoice.
- TOTP generation requires a valid secret and synchronized system time.

## Future Improvements

- Add a single entry point for the complete GitHub authentication workflow.
- Expand tests for expired and corrupted sessions.
- Add offline HTML fixtures for locator regression testing.
- Improve failure-evidence redaction.
- Add CI checks for non-interactive tests.

## License

No license is specified for this assignment.
