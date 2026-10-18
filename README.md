# Playwright 2FA Session Automation



A Python automation project using Playwright to authenticate with a portal, reuse browser sessions, navigate multi-page workflows, interact with dependent form fields, capture a document, and produce structured execution evidence.



## Features



- Automated GitHub login with TOTP-based two-factor authentication.

- Persistent browser session storage and reuse.

- Session validation and re-authentication when a saved session is invalid or expired.

- Amazon order workflow with PIN-dependent city and state verification.

- Invoice PDF capture.

- Locator resolver with role/name, label, nearby text, structural, ID, and class strategies.

- Bounded retries with exponential backoff for configured transient failures.

- Failure evidence including screenshot, sanitized HTML, metadata, console logs, and locator attempts.

- JSON manifest containing workflow status, pages visited, timings, and captured files.



## Requirements



- Python 3.14 or a compatible supported Python version

- Chromium supported by the installed Playwright version

- Git

- GitHub account with TOTP enabled for the GitHub authentication workflow

- Amazon account with access to the relevant orders for the Amazon workflow



## Setup



Create and activate a virtual environment.



### Windows PowerShell



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt

python -m playwright install chromium

```



## Configuration



Create a local `.env` file in the project root. Do not commit it.



For the GitHub workflow, configure:



```text

GITHUB\_USERNAME=your\_username

GITHUB\_PASSWORD=your\_password

GITHUB\_TOTP\_SECRET=your\_totp\_secret

```



Use your own values locally. Never put credentials, TOTP secrets, one-time codes, recovery codes, or browser cookies in source files or logs.



The TOTP secret must be configured securely from your own authenticator setup. Do not share it with reviewers.



## Running the Amazon workflow



Review `input.json` before running. It controls the portal, address-check inputs, invoice capture, and output directory.



Run:



```powershell

python .\\amazon\_workflow.py

```



The workflow uses the saved Amazon browser state when available. If authentication is required, complete the portal's sign-in and verification steps in the browser.



The address check reads the PIN-dependent location fields but does not save an address.



## Outputs



- `downloads/order\_invoice.pdf` â€” captured invoice document.

- `artifacts/manifest.json` â€” workflow result, visited pages, dependent field values, timings, and captured file paths.

- `artifacts/failures/` â€” diagnostic evidence for failed runs.



Generated outputs and authenticated session state are excluded by `.gitignore` by default. Only publish a document if it has been reviewed for personal or confidential information.



## Authentication and session behavior



The GitHub authentication flow generates TOTP codes locally using `pyotp`. Codes and secrets must never be logged.



The session manager validates the saved storage-state structure and checks access to a protected GitHub page. If the session is not authenticated, the browser manager starts a new login flow and saves the refreshed session after authentication.



The TOTP retry logic permits one additional attempt only when an explicit rejection is detected. The current offline tests use mocks to verify retry decisions; live error-message detection depends on the portal's page markup.



## Locator resolution



The resolver tries these strategies in order:



1\. Role and accessible name

2\. Label

3\. Nearby text

4\. Structural relationship

5\. Element ID

6\. CSS class



It records the attempted strategies, match counts, statuses, and winning strategy. It avoids silently selecting an arbitrary element when a unique match cannot be found.



Offline tests use saved HTML so locator behavior can be checked without repeatedly accessing a live portal.



## Retry and failure handling



Retries are bounded and use exponential backoff. Only explicitly configured transient exceptions should be retried; authentication failures and other non-transient errors should be handled separately.



When a workflow fails, the failure-evidence module attempts to save:



- Screenshot

- Sanitized page HTML

- JSON metadata with stage and error details

- Available console logs

- Locator resolver attempts



Evidence files can still contain sensitive page content or visual information. Review them before sharing publicly.



## Tests



Run the core offline tests individually:



```powershell

python .\\test\_totp\_helper.py

python .\\test\_auth\_totp\_retry.py

python .\\test\_session\_manager.py

python .\\test\_browser\_manager.py

python .\\test\_locator\_resolver.py

python .\\test\_failure\_evidence.py

python .\\test\_locator\_failure\_evidence.py

python .\\test\_retry\_utils.py

```



Some tests create local files under `artifacts/`. These are generated outputs and are ignored by Git by default.



The authentication retry tests mock portal responses. They do not replace a final end-to-end verification against a test account or live portal.



## Security notes



- Never commit `.env`, authentication state files, cookies, or TOTP secrets.

- Review invoices, screenshots, HTML evidence, and manifests before publishing.

- Use test accounts and test data where possible.

- Do not publish personal order information or private account URLs.

- Revoke and rotate any credential accidentally exposed in a public repository.



## Limitations



Portal page structure and authentication behavior can change. Selectors and error-message detection may need updates when the portal changes. Verify the workflow against the current portal before relying on it for unattended execution.



This project is an automation demonstration and should be adapted and tested before use with other portals.
