
"""Offline tests for browser session detection."""

from unittest.mock import Mock, patch

import browser_manager


def test_valid_session_is_reused():
    playwright = Mock()
    browser = Mock()
    context = Mock()
    page = Mock()

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    with (
        patch.object(browser_manager, "is_session_state_valid", return_value=True),
        patch.object(browser_manager, "is_github_session_authenticated", return_value=True),
        patch.object(browser_manager, "save_session_state") as save_state,
        patch.object(browser_manager, "login") as login,
        patch.object(browser_manager, "clear_session_state") as clear_state,
    ):
        result_browser, result_context, result_page, authenticated = (
            browser_manager.create_browser_context(playwright)
        )

    assert result_browser is browser
    assert result_context is context
    assert result_page is page
    assert authenticated is True
    login.assert_not_called()
    save_state.assert_not_called()
    clear_state.assert_not_called()

    print("Valid-session reuse test passed")


def test_invalid_session_triggers_login():
    playwright = Mock()
    browser = Mock()
    context = Mock()
    page = Mock()

    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page

    with (
        patch.object(browser_manager, "is_session_state_valid", return_value=False),
        patch.object(browser_manager, "is_github_session_authenticated", return_value=False),
        patch.object(browser_manager, "login", return_value="authenticated") as login,
        patch.object(browser_manager, "save_session_state") as save_state,
    ):
        result = browser_manager.create_browser_context(playwright)

    assert result[3] is True
    login.assert_called_once_with(page)
    save_state.assert_called_once_with(context)

    print("Invalid-session login test passed")


if __name__ == "__main__":
    test_valid_session_is_reused()
    test_invalid_session_triggers_login()
