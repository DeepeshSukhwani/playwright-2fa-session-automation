
"""Fallback locator resolver for Playwright pages."""

import logging
import re

from playwright.sync_api import Page

logger = logging.getLogger("github_automation")


def resolve_locator(
        page: Page,
        *,
        role: str | None = None,
        name: str | None = None,
        label: str | None = None,
        nearby_text: str | None = None,
        tag: str | None = None,
        element_id: str | None = None,
        class_name: str | None = None,
) -> tuple[object | None, dict]:
    """Find exactly one element and record every attempted strategy."""

    attempts = []
    candidates = []

    if role and name:
        candidates.append((
            "role_name",
            lambda: page.get_by_role(role, name=name, exact=True),
        ))

    if label:
        candidates.append((
            "label",
            lambda: page.get_by_label(label, exact=isinstance(label, str)),
        ))

    if nearby_text:
        def find_input_near_text():
            text_locator = page.get_by_text(nearby_text, exact=True)

            if text_locator.count() != 1:
                return text_locator.locator("xpath=..").locator(
                    "input, textarea, select"
                ).filter(visible=True)

            # Search the text element's parent for form controls.
            parent = text_locator.locator("xpath=..")
            controls = parent.locator("input, textarea, select")

            if controls.count() == 1:
                return controls

            # Do not return the text itself as though it were an input.
            return page.locator("input[data-resolver-no-match]")

        candidates.append(("nearby_text", find_input_near_text))

    if tag:
        candidates.append((
            "structure",
            lambda: page.locator(tag),
        ))

    if element_id:
        candidates.append((
            "id",
            lambda: page.locator(f"#{element_id}"),
        ))

    if class_name:
        safe_class = re.sub(r"[^a-zA-Z0-9_-]", "", class_name)

        if safe_class:
            candidates.append((
                "class",
                lambda selector=f".{safe_class}": page.locator(selector),
            ))

    for strategy, build_locator in candidates:
        try:
            locator = build_locator()
            count = locator.count()

            if count == 1:
                status = "matched"
            elif count == 0:
                status = "no_match"
            else:
                status = "multiple_matches"

            attempts.append({
                "strategy": strategy,
                "match_count": count,
                "status": status,
            })

            if status == "matched":
                logger.info(
                    "Locator resolved using strategy: %s", strategy
                )
                return locator, {
                    "success": True,
                    "winning_strategy": strategy,
                    "attempts": attempts,
                }

        except Exception as exc:
            attempts.append({
                "strategy": strategy,
                "status": "error",
                "error_type": type(exc).__name__,
            })

    logger.warning("No locator strategy found a unique match")

    return None, {
        "success": False,
        "winning_strategy": None,
        "attempts": attempts,
    }
