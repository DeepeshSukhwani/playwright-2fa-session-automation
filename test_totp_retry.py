
"""Offline tests for the one-time TOTP retry policy."""


def should_retry_totp(rejected: bool, attempts: int) -> bool:
    """Retry once only when the site explicitly rejects the code."""
    return rejected and attempts == 1


def main() -> None:
    assert should_retry_totp(rejected=True, attempts=1) is True
    assert should_retry_totp(rejected=True, attempts=2) is False
    assert should_retry_totp(rejected=False, attempts=1) is False
    assert should_retry_totp(rejected=False, attempts=2) is False

    print("TOTP retry policy tests passed")


if __name__ == "__main__":
    main()
