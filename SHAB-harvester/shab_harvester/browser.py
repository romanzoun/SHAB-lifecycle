from __future__ import annotations

from contextlib import contextmanager

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from . import config

BASE_URL = "https://www.shab.ch/#!/search/publications"

CUSTOM_PERIOD_RADIO = "#select-date-range"
START_DATE_INPUT = "#startDate"
END_DATE_INPUT = "#endDate"
SEARCH_TRIGGER = "#execute"

RESULTS_ROOT = "publication-search-results"
TOTAL_COUNT = "#totalItemsCount strong"
RESULT_ENTRY = "publication-list .list-entry"
RESULT_INFO = ".publication-info .list-col"
RESULT_TITLE_LINK = "h2 a"

DETAIL_METADATA_ROOT = "publication-metadata"
DETAIL_METADATA_DL = "publication-metadata dl"
DETAIL_CONTENT_ROOT = "publication-content"
DETAIL_HEADLINE = "publication-content .app-content-headline"
DETAIL_FIELD_VALUE = "publication-content .field-value"
DETAIL_ACTIONS_ROOT = "publication-search-actions"
DETAIL_ACTION_LINKS = "publication-search-actions a"

BLOCKED_RESOURCE_TYPES = {"image", "font", "media"}


def _route_handler(route):
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        route.abort()
    else:
        route.continue_()


@contextmanager
def launch_browser(headless: bool = False):
    with sync_playwright() as playwright:
        browser: Browser = playwright.chromium.launch(headless=headless)
        try:
            yield browser
        finally:
            browser.close()


@contextmanager
def new_context(browser: Browser):
    context: BrowserContext = browser.new_context()
    context.route("**/*", _route_handler)
    try:
        yield context
    finally:
        context.close()


def dismiss_consent_banner(page: Page) -> None:
    """Click an accept/close button on a cookie/consent banner if one is visible."""
    candidates = [
        "button:has-text('Accept')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Schliessen')",
        "button:has-text('Close')",
        "[aria-label='close']",
        ".cc-allow",
    ]
    for selector in candidates:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=500):
                locator.click(timeout=1000)
                return
        except Exception:
            continue


def _nudge_results_scroll(page: Page) -> None:
    """Scroll window *and* likely results containers.

    SHAB's infinite-scroll often listens on an inner list, not `window`.
    Scrolling only `document.body` stops after the first ~100 hits.
    """
    page.evaluate(
        """() => {
            window.scrollTo(0, document.body.scrollHeight);
            const roots = [
                document.querySelector('publication-search-results'),
                document.querySelector('publication-list'),
                document.querySelector('.mat-drawer-content'),
                document.querySelector('.cdk-virtual-scroll-viewport'),
                document.scrollingElement,
            ].filter(Boolean);
            for (const el of roots) {
                try {
                    el.scrollTop = el.scrollHeight;
                    el.dispatchEvent(new Event('scroll', { bubbles: true }));
                } catch (e) {}
            }
        }"""
    )


def scroll_results_one_step(page: Page) -> bool:
    """Advance result lists by about one viewport. Returns True when every
    scrollable root is already at the bottom (nothing moved)."""
    return bool(
        page.evaluate(
            """() => {
                const roots = [
                    document.querySelector('publication-search-results'),
                    document.querySelector('publication-list'),
                    document.querySelector('.mat-drawer-content'),
                    document.querySelector('.cdk-virtual-scroll-viewport'),
                    document.scrollingElement,
                ].filter(Boolean);
                let atBottom = true;
                for (const el of roots) {
                    const max = (el.scrollHeight || 0) - (el.clientHeight || 0);
                    if (max <= 4) continue;
                    const step = Math.max(240, Math.floor((el.clientHeight || 600) * 0.65));
                    const next = Math.min((el.scrollTop || 0) + step, max);
                    if (next > (el.scrollTop || 0) + 2) {
                        el.scrollTop = next;
                        el.dispatchEvent(new Event('scroll', { bubbles: true }));
                        atBottom = false;
                    } else if ((el.scrollTop || 0) < max - 4) {
                        atBottom = false;
                    }
                }
                return atBottom;
            }"""
        )
    )


def scroll_until_all_loaded(
    page: Page,
    expected_count: int,
    max_rounds: int = config.SCROLL_MAX_ROUNDS,
    wait_ms: int = config.SCROLL_WAIT_MS,
    stable_rounds_threshold: int = config.SCROLL_STABLE_ROUNDS,
) -> int:
    # ~50–100 items per lazy page; allow enough rounds for large days.
    if expected_count and expected_count > 0:
        max_rounds = max(max_rounds, (expected_count // 25) + 40)

    last_count = -1
    stable_rounds = 0
    for _ in range(max_rounds):
        current_count = page.locator(RESULT_ENTRY).count()
        if expected_count and current_count >= expected_count:
            return current_count
        if current_count == last_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        # Far below expected: do not give up after a few idle rounds (classic
        # false stop at ~100). Only accept "stable" early when nearly complete.
        if expected_count and current_count < int(expected_count * 0.98):
            need_stable = stable_rounds_threshold * 6
        else:
            need_stable = stable_rounds_threshold
        if stable_rounds >= need_stable:
            return current_count
        last_count = current_count
        _nudge_results_scroll(page)
        page.wait_for_timeout(wait_ms)
    return page.locator(RESULT_ENTRY).count()
