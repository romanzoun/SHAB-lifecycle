from __future__ import annotations

import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request

from playwright.sync_api import Page

from . import browser as br
from . import config
from . import db
from .utils import (
    extract_date_from_list_info,
    extract_publication_number,
    to_ddmmyyyy,
)

PUBLICATIONS_API = "https://www.shab.ch/api/v1/publications"
# Same rubric set and states the SHAB search page sends. The stored
# result_count comes from that filtered total.
SEARCH_RUBRICS = "AB,AW,AZ,BB,BH,EK,ES,FM,HR,KK,LS,NA,SB,SR,UP,UV"
SEARCH_STATES = "PUBLISHED,CANCELLED"
# Stable order. Unsorted pages overlap, so unique ids stay below `total`.
SEARCH_SORT = "column:PUBLICATION_NUMBER|direction:ASC"


class DiscoveryError(RuntimeError):
    pass


def read_total_count(page: Page) -> int:
    """Fallback only: reads the DOM's #totalItemsCount text. Unreliable on
    its own — see read_filtered_total below for why."""
    locator = page.locator(br.TOTAL_COUNT)
    if locator.count() == 0:
        return 0
    text = locator.first.inner_text()
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def read_filtered_total(page: Page, publication_date: str, trigger) -> int:
    """Reads the authoritative result count straight from the date-filtered
    API response, not the DOM.

    The #totalItemsCount text initially reflects the *unfiltered* page load
    (all-time count, e.g. 2.7M) and only updates once a request carrying our
    date filter actually completes — which the SPA only fires once the
    results list is scrolled, and not necessarily as the very first page.
    Reading the DOM before that response lands silently returns the
    all-time total instead of 0/N for this day. `trigger` is called inside
    the wait so the caller can both apply the filter and nudge the
    infinite-scroll directive to fire the first filtered request.
    """
    date_param = f"publicationDate.start={publication_date}"
    try:
        with page.expect_response(
            lambda r: date_param in r.url, timeout=config.FILTERED_RESPONSE_TIMEOUT_MS
        ) as response_info:
            trigger()
        return response_info.value.json().get("total", 0)
    except Exception:
        # If SHAB's API shape ever changes, fall back to the old DOM-polling
        # behavior rather than failing the whole day outright.
        previous = None
        for _ in range(10):
            page.wait_for_timeout(300)
            current = read_total_count(page)
            if previous is not None and current == previous:
                return current
            previous = current
        return previous if previous is not None else 0


def merge_result_items(seen: dict[str, dict], items: list[dict]) -> int:
    """Keep the first sighting of each publication id. Virtual scroll drops
    rows from the DOM, so a final query never sees the whole day."""
    added = 0
    for item in items:
        publication_id = item.get("publication_id")
        if not publication_id or publication_id in seen:
            continue
        seen[publication_id] = item
        added += 1
    return added


def collect_results_while_scrolling(
    page: Page,
    expected_count: int,
    max_rounds: int | None = None,
    wait_ms: int = config.SCROLL_WAIT_MS,
    stable_rounds_threshold: int = config.SCROLL_STABLE_ROUNDS,
) -> list[dict]:
    """Scroll in steps and accumulate unique result rows.

    SHAB only keeps a window of rows mounted. Counting DOM nodes at the end
    stops around 85–95% of result_count and never grows on retry.
    """
    if expected_count and expected_count > 0:
        rounds = max(config.SCROLL_MAX_ROUNDS, (expected_count // 15) + 60)
    else:
        rounds = config.SCROLL_MAX_ROUNDS
    if max_rounds is not None:
        rounds = max_rounds

    seen: dict[str, dict] = {}
    last_count = 0
    stable_rounds = 0
    for _ in range(rounds):
        merge_result_items(seen, extract_result_items(page))
        current = len(seen)
        if expected_count and current >= expected_count:
            return list(seen.values())
        if current == last_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        at_bottom = br.scroll_results_one_step(page)
        if expected_count and current < int(expected_count * 0.98):
            need_stable = stable_rounds_threshold * 8
        else:
            need_stable = stable_rounds_threshold
        # Only stop on a stable count once the list will not scroll further.
        # Otherwise a virtual window looks "full" while later pages are unloaded.
        if at_bottom and stable_rounds >= need_stable:
            return list(seen.values())
        last_count = current
        page.wait_for_timeout(wait_ms)
    merge_result_items(seen, extract_result_items(page))
    return list(seen.values())


def extract_result_items(page: Page) -> list[dict]:
    return page.locator(br.RESULT_ENTRY).evaluate_all(
        """
        els => els.map(el => {
            const link = el.querySelector("h2 a");
            const info = el.querySelector(".publication-info .list-col");
            return {
                publication_id: el.id || null,
                list_info: info ? info.innerText.trim().replace(/\\s+/g, " ") : null,
                title: link ? link.innerText.trim().replace(/\\s+/g, " ") : null,
                detail_href: link ? link.getAttribute("href") : null
            };
        })
        """
    )


def set_date_filter(page: Page, day_ddmmyyyy: str) -> None:
    page.locator(br.CUSTOM_PERIOD_RADIO).check()

    # Angular's datepicker model only updates on real keystrokes; fill() bypasses
    # the input events the directive listens for, so the search silently ignores
    # the date and returns the unfiltered result set.
    #
    # When the page (and thus the Angular app) is reused across consecutive
    # discover_day calls (discover-pending-days, harvest-range), the fields
    # already hold the previous day's value. A plain click + Control+A does
    # NOT reliably select that pre-filled text here (focus can land on the
    # datepicker popup instead of the input), so the new date gets appended
    # instead of replacing it (e.g. "03.09.201802.09.2018"), silently
    # producing an invalid range and 0 results. A triple-click reliably
    # selects the whole field's text regardless of that.
    for selector in (br.START_DATE_INPUT, br.END_DATE_INPUT):
        page.click(selector, click_count=3)
        page.keyboard.type(day_ddmmyyyy)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)

    page.locator(br.SEARCH_TRIGGER).dispatch_event("click")


def _title_from_meta(meta: dict) -> str | None:
    titles = meta.get("title") or {}
    if not isinstance(titles, dict):
        return None
    lang = str(meta.get("language") or "").lower()
    if titles.get(lang):
        return str(titles[lang]).strip() or None
    for key in ("de", "fr", "it", "en"):
        if titles.get(key):
            return str(titles[key]).strip() or None
    return None


def publication_from_api_item(item: dict, fallback_date: str) -> dict | None:
    """Map one search-API hit onto the queue fields discovery already stores."""
    meta = item.get("meta") or {}
    publication_id = meta.get("id")
    if not publication_id:
        return None
    raw_date = str(meta.get("publicationDate") or "")
    publication_date = raw_date[:10] if len(raw_date) >= 10 else fallback_date
    number = meta.get("publicationNumber")
    rubric = meta.get("subRubric") or meta.get("rubric")
    try:
        day_label = to_ddmmyyyy(publication_date)
    except ValueError:
        day_label = None
        publication_date = fallback_date
    list_info = " - ".join(part for part in (day_label, number, rubric) if part) or None
    return {
        "publication_id": publication_id,
        "publication_date": publication_date,
        "publication_number": number,
        "title": _title_from_meta(meta),
        "list_info": list_info,
        "detail_url": f"https://www.shab.ch/#!/search/publications/detail/{publication_id}",
    }


def publications_api_url(publication_date: str, page_index: int) -> str:
    query = urllib.parse.urlencode(
        {
            "allowRubricSelection": "false",
            "includeContent": "false",
            "pageRequest.page": str(page_index),
            "pageRequest.size": str(config.DISCOVERY_PAGE_SIZE),
            "pageRequest.sortOrders": SEARCH_SORT,
            "publicationDate.start": publication_date,
            "publicationDate.end": publication_date,
            "publicationStates": SEARCH_STATES,
            "rubrics": SEARCH_RUBRICS,
            "searchPeriod": "CUSTOM",
        }
    )
    return f"{PUBLICATIONS_API}?{query}"


def fetch_publications_page(publication_date: str, page_index: int) -> dict:
    url = publications_api_url(publication_date, page_index)
    last_error: Exception | None = None
    for attempt in range(config.DISCOVERY_PAGE_RETRIES):
        try:
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "shab-harvester"},
            )
            with urllib.request.urlopen(request, timeout=config.DISCOVERY_HTTP_TIMEOUT_S) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise DiscoveryError("publication API returned a non-object payload")
            return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
        if attempt + 1 < config.DISCOVERY_PAGE_RETRIES:
            time.sleep(1.0 * (attempt + 1))
    raise DiscoveryError(f"publication API failed for {publication_date} page {page_index}: {last_error}")


def collect_day_from_api(publication_date: str) -> tuple[int, list[dict]]:
    """Walk sorted API pages until `total` unique publications are collected."""
    seen: dict[str, dict] = {}
    total: int | None = None
    page_index = 0
    while True:
        payload = fetch_publications_page(publication_date, page_index)
        if total is None:
            total = int(payload.get("total") or 0)
            if total > config.DISCOVERY_MAX_DAY_TOTAL:
                raise DiscoveryError(
                    f"refusing total {total} for {publication_date}; "
                    "that is larger than one publication day"
                )
            if total == 0:
                return 0, []
        content = payload.get("content") or []
        if not isinstance(content, list):
            raise DiscoveryError(f"publication API content is not a list for {publication_date}")
        for raw in content:
            if not isinstance(raw, dict):
                continue
            mapped = publication_from_api_item(raw, publication_date)
            if mapped is None:
                continue
            seen.setdefault(mapped["publication_id"], mapped)
        page_index += 1
        if not content or len(seen) >= total:
            break
        max_pages = (total + config.DISCOVERY_PAGE_SIZE - 1) // config.DISCOVERY_PAGE_SIZE + 1
        if page_index >= max_pages:
            break
        time.sleep(config.DISCOVERY_PAGE_PAUSE_S)
    return total, list(seen.values())


def discover_day(conn: sqlite3.Connection, publication_date: str) -> None:
    db.mark_day_running(conn, publication_date)
    conn.commit()

    count, items = collect_day_from_api(publication_date)

    if count == 0:
        db.mark_day_empty(conn, publication_date)
        conn.commit()
        return

    warning = None
    if len(items) < count:
        warning = f"only {len(items)}/{count} unique entries collected from the search API"

    for item in items:
        list_info = item.get("list_info")
        publication_number = item.get("publication_number") or extract_publication_number(list_info)
        item_date = item.get("publication_date") or extract_date_from_list_info(list_info) or publication_date
        db.upsert_queue_item(
            conn,
            publication_id=item["publication_id"],
            publication_date=item_date,
            publication_number=publication_number,
            title=item.get("title"),
            list_info=list_info,
            detail_url=item.get("detail_url"),
        )

    db.mark_day_discovered(conn, publication_date, count, len(items), warning=warning)
    conn.commit()
