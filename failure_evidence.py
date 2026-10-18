
"""Capture diagnostic evidence when a Playwright stage fails."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from config import BASE_DIR

logger = logging.getLogger("github_automation")

EVIDENCE_DIR = BASE_DIR / "artifacts" / "failures"

SENSITIVE_TEXT = re.compile(
    r"""(?ix)
    (password|passwd|otp|one.time.password|totp|
     access.token|refresh.token|secret|authorization|
     cookie|credential|api.key)
    (\s*["']?\s*[:=]\s*["']?)[^\s"',;}]+
    """
)

SENSITIVE_QUERY_KEYS = re.compile(
    r"token|code|otp|password|secret|session|auth|email|phone|"
    r"account|customer|address|cookie|credential|key",
    re.I,
)


def safe_url(url: str) -> str:
    """Remove query parameters, fragments, and URL credentials."""
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""

        if parts.port:
            host = f"{host}:{parts.port}"

        return urlunsplit(
            (parts.scheme, host, parts.path, "", "")
        )
    except (ValueError, TypeError):
        return "[URL unavailable]"


def redact_text(value: str) -> str:
    """Redact common secret values from diagnostic text."""
    value = SENSITIVE_TEXT.sub(r"\1\2[REDACTED]", value)

    # Redact common HTML form input values.
    value = re.sub(
        r"""(?is)(<input\b[^>]*\bvalue\s*=\s*)(["']).*?\2""",
        r'\1"\2[REDACTED]\2',
        value,
    )

    return value


def capture_failure_evidence(
        page,
        stage: str,
        error: Exception,
        resolver_attempts: list | None = None,
) -> dict:
    """Save a screenshot, sanitized HTML, and diagnostic metadata."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stage_name = re.sub(r"[^a-zA-Z0-9_-]", "_", stage)[:50]
    prefix = f"{timestamp}_{stage_name}"

    result = {
        "stage": stage,
        "timestamp_utc": timestamp,
        "url": safe_url(getattr(page, "url", "")),
        "error_type": type(error).__name__,
        "error_message": redact_text(str(error)),
        "screenshot": None,
        "html": None,
        "console_logs": [],
        "resolver_attempts": resolver_attempts or [],
    }

    try:
        screenshot_path = EVIDENCE_DIR / f"{prefix}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot"] = str(
            screenshot_path.relative_to(BASE_DIR)
        )
    except Exception as exc:
        logger.warning(
            "Could not capture failure screenshot: %s",
            type(exc).__name__,
        )

    try:
        html = redact_text(page.content())

        html_path = EVIDENCE_DIR / f"{prefix}.html"
        html_path.write_text(html, encoding="utf-8")
        result["html"] = str(html_path.relative_to(BASE_DIR))
    except Exception as exc:
        logger.warning(
            "Could not capture failure HTML: %s",
            type(exc).__name__,
        )

    try:
        logs = getattr(page, "_failure_console_logs", [])
        result["console_logs"] = [
            redact_text(str(message)) for message in logs
        ]
    except Exception as exc:
        logger.warning(
            "Could not capture console logs: %s",
            type(exc).__name__,
        )

    # Resolver attempts can contain text derived from page content.
    # Redact their serialized representation before saving.
    try:
        attempts_json = json.dumps(result["resolver_attempts"])
        result["resolver_attempts"] = json.loads(
            redact_text(attempts_json)
        )
    except (TypeError, ValueError):
        result["resolver_attempts"] = ["[Resolver details unavailable]"]

    metadata_path = EVIDENCE_DIR / f"{prefix}.json"
    metadata_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    logger.error(
        "Failure evidence captured for stage %s: %s",
        stage_name,
        metadata_path.relative_to(BASE_DIR),
    )

    return result
