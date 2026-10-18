
"""Test retry limits and recovery from a transient failure."""

from unittest.mock import patch

from retry_utils import retry_transient


class TemporaryFailure(Exception):
    """Represents a retryable test failure."""


def main():
    attempts = {"count": 0}

    def flaky_operation():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TemporaryFailure("Temporary test failure")
        return "success"

    with patch("retry_utils.time.sleep") as sleep_mock:
        result = retry_transient(
            flaky_operation,
            retryable_exceptions=(TemporaryFailure,),
            max_attempts=3,
            base_delay_seconds=0.1,
        )

    assert result == "success"
    assert attempts["count"] == 3
    assert sleep_mock.call_count == 2

    print("Retry utility tests passed")


if __name__ == "__main__":
    main()
