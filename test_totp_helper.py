
"""Test TOTP generation using a dummy secret."""

import re
from unittest.mock import patch

from totp_helper import generate_totp_code


def main():
    # Missing configuration must fail safely.
    with patch("totp_helper.GITHUB_TOTP_SECRET", ""):
        try:
            generate_totp_code()
        except ValueError:
            pass
        else:
            raise AssertionError("Missing secret should be rejected")

    # A dummy secret verifies generation without using a real account.
    with patch("totp_helper.GITHUB_TOTP_SECRET", "JBSWY3DPEHPK3PXP"):
        code = generate_totp_code()
        assert re.fullmatch(r"\d{6}", code), "Expected a six-digit code"

    print("TOTP helper tests passed")


if __name__ == "__main__":
    main()
