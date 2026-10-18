
"""Generate GitHub TOTP codes from a local environment secret."""

import logging

import pyotp

from config import GITHUB_TOTP_SECRET

logger = logging.getLogger("github_automation")


def generate_totp_code() -> str:
    """Generate the current TOTP code without logging the secret or code."""
    if not GITHUB_TOTP_SECRET:
        raise ValueError("GITHUB_TOTP_SECRET is not configured")

    try:
        totp = pyotp.TOTP(GITHUB_TOTP_SECRET)
        code = totp.now()
    except (ValueError, TypeError) as exc:
        raise ValueError("TOTP configuration is invalid") from exc

    logger.info("Generated a TOTP code")
    return code
