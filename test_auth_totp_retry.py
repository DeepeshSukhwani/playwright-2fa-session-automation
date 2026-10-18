
"""Offline tests for the actual TOTP retry flow."""

from unittest.mock import Mock, call, patch

import auth


def make_page():
    page = Mock()
    code_input = Mock()
    verify_button = Mock()

    page.locator.return_value = code_input
    page.get_by_role.return_value = verify_button

    # Simulate Playwright's navigation context manager.
    navigation = Mock()
    navigation.__enter__ = Mock(return_value=None)
    navigation.__exit__ = Mock(return_value=False)
    page.expect_navigation.return_value = navigation

    return page, code_input, verify_button


def test_rejected_code_retries_once():
    page, code_input, verify_button = make_page()

    with (
        patch.object(
            auth, "generate_totp_code",
            side_effect=["111111", "222222"],
        ) as generate_code,
        patch.object(
            auth, "_verify_authenticated_session",
            side_effect=["not_authenticated", "authenticated"],
        ),
        patch.object(auth, "_has_totp_rejection", return_value=True),
    ):
        result = auth._submit_totp(page)

    assert result == "authenticated"
    assert generate_code.call_count == 2
    assert code_input.fill.call_args_list == [
        call("111111"),
        call("222222"),
    ]
    assert verify_button.click.call_count == 2
    assert page.go_back.call_count == 1

    print("Rejected-code retry test passed")


def test_no_retry_without_explicit_rejection():
    page, code_input, verify_button = make_page()

    with (
        patch.object(
            auth, "generate_totp_code", return_value="111111"
        ) as generate_code,
        patch.object(
            auth, "_verify_authenticated_session",
            return_value="not_authenticated",
        ),
        patch.object(auth, "_has_totp_rejection", return_value=False),
    ):
        result = auth._submit_totp(page)

    assert result == "not_authenticated"
    assert generate_code.call_count == 1
    assert verify_button.click.call_count == 1
    assert page.go_back.call_count == 0

    print("No-retry-without-rejection test passed")


if __name__ == "__main__":
    test_rejected_code_retries_once()
    test_no_retry_without_explicit_rejection()
