from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from playwright.sync_api import Page

from . import browser as br
from . import config
from . import db
from .utils import (
    JOURNAL_RE,
    PREVIOUS_PUBLICATION_RE,
    UID_RE,
    UUID_RE,
    content_hash,
    now_iso,
    year_month,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_HTML_DIR = DATA_DIR / "raw_html"
RAW_XML_DIR = DATA_DIR / "raw_xml"


class RateLimitError(Exception):
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"Rate limited with HTTP {status}")


def extract_metadata(page: Page) -> dict:
    if page.locator(br.DETAIL_METADATA_DL).count() == 0:
        return {}
    return page.locator(br.DETAIL_METADATA_DL).evaluate(
        """
        dl => {
            const result = {};
            let currentKey = null;
            for (const child of dl.children) {
                const tag = child.tagName.toLowerCase();
                const text = child.innerText.trim().replace(/\\s+/g, " ");
                if (!text) continue;
                if (tag === "dt") {
                    currentKey = text;
                    if (!result[currentKey]) result[currentKey] = [];
                } else if (currentKey) {
                    if (!result[currentKey].includes(text)) {
                        result[currentKey].push(text);
                    }
                }
            }
            return result;
        }
        """
    )


def extract_content(page: Page) -> dict:
    if page.locator(br.DETAIL_CONTENT_ROOT).count() == 0:
        return {"headline": None, "field_values": [], "text": "", "html": ""}
    return page.locator(br.DETAIL_CONTENT_ROOT).evaluate(
        """
        el => {
            const headline = el.querySelector(".app-content-headline")?.innerText?.trim().replace(/\\s+/g, " ") || null;
            const fieldValues = Array.from(el.querySelectorAll(".field-value"))
                .map(x => x.innerText.trim().replace(/\\s+/g, " "))
                .filter(Boolean);
            return {
                headline,
                field_values: fieldValues,
                text: fieldValues.join("\\n"),
                html: el.innerHTML
            };
        }
        """
    )


def extract_links(page: Page) -> list[dict]:
    if page.locator(br.DETAIL_ACTIONS_ROOT).count() == 0:
        return []
    return page.locator(br.DETAIL_ACTION_LINKS).evaluate_all(
        """
        els => els.map(a => ({
            text: a.innerText.trim().replace(/\\s+/g, " "),
            href: a.href
        }))
        """
    )


def parse_links(links: list[dict], content_text: str) -> dict:
    xml_url = None
    pdf_url = None
    zefix_url = None
    uid = None
    for link in links:
        text = link.get("text") or ""
        href = link.get("href") or ""
        m = UUID_RE.search(href)
        if m and "/xml" in href:
            xml_url = href
        elif m and "/pdf" in href:
            pdf_url = href
        if "zefix.admin.ch" in href:
            zefix_url = href
        if uid is None:
            uid_match = UID_RE.search(text + " " + href)
            if uid_match:
                uid = uid_match.group(0)
    if uid is None:
        uid_match = UID_RE.search(content_text or "")
        if uid_match:
            uid = uid_match.group(0)
    return {"xml_url": xml_url, "pdf_url": pdf_url, "zefix_url": zefix_url, "uid": uid}


def derive_company_and_body(field_values: list[str]) -> tuple[str | None, str | None]:
    company_block_text = field_values[0] if field_values else None
    body_text = None
    for value in field_values:
        if UID_RE.search(value):
            body_text = value
            break
    if body_text is None and field_values:
        body_text = max(field_values, key=len)
    return company_block_text, body_text


def parse_journal_and_previous(text: str) -> dict:
    result = {
        "journal_number": None,
        "journal_date": None,
        "previous_sogc_number": None,
        "previous_sogc_date": None,
    }
    m = JOURNAL_RE.search(text or "")
    if m:
        result["journal_number"] = m.group(1)
        result["journal_date"] = m.group(2)
    m = PREVIOUS_PUBLICATION_RE.search(text or "")
    if m:
        result["previous_sogc_number"] = m.group(1)
        result["previous_sogc_date"] = m.group(2)
    return result


def fetch_and_store_xml(context, xml_url: str, publication_id: str, publication_date: str, force: bool) -> tuple[str | None, str | None]:
    year, month = year_month(publication_date) if publication_date else ("unknown", "unknown")
    target_dir = RAW_XML_DIR / year / month
    target_path = target_dir / f"{publication_id}.xml"
    if target_path.exists() and not force:
        return str(target_path.relative_to(DATA_DIR.parent)), None
    try:
        response = context.request.get(xml_url)
        if response.status == 200:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(response.body())
            return str(target_path.relative_to(DATA_DIR.parent)), None
        return None, f"xml fetch failed with HTTP {response.status}"
    except Exception as exc:  # network errors must not fail the whole publication
        return None, f"xml fetch error: {exc}"


def save_page_html(page: Page, publication_id: str, publication_date: str, force: bool) -> str:
    year, month = year_month(publication_date) if publication_date else ("unknown", "unknown")
    target_dir = RAW_HTML_DIR / year / month
    target_path = target_dir / f"{publication_id}.html"
    if target_path.exists() and not force:
        return str(target_path.relative_to(DATA_DIR.parent))
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path.write_text(page.content(), encoding="utf-8")
    return str(target_path.relative_to(DATA_DIR.parent))


def first(metadata: dict, key: str) -> str | None:
    values = metadata.get(key)
    return values[0] if values else None


def scrape_publication_detail(
    conn: sqlite3.Connection,
    page: Page,
    publication_id: str,
    publication_date: str,
    detail_url: str | None,
    force: bool = False,
) -> None:
    url = detail_url or f"https://www.shab.ch/#!/search/publications/detail/{publication_id}"
    response = page.goto(url, wait_until="networkidle")
    if response is not None and response.status in (403, 429):
        raise RateLimitError(response.status)

    page.wait_for_selector(br.DETAIL_METADATA_ROOT, timeout=config.PAGE_TIMEOUT_MS)
    page.wait_for_selector(br.DETAIL_CONTENT_ROOT, timeout=config.PAGE_TIMEOUT_MS)
    page.wait_for_selector(br.DETAIL_ACTIONS_ROOT, timeout=config.PAGE_TIMEOUT_MS)

    metadata = extract_metadata(page)
    content = extract_content(page)
    links = extract_links(page)
    parsed_links = parse_links(links, content.get("text", ""))
    company_block_text, body_text = derive_company_and_body(content.get("field_values", []))
    journal_info = parse_journal_and_previous(content.get("text", ""))

    raw_page_html_path = save_page_html(page, publication_id, publication_date, force)

    raw_xml_path = None
    xml_warning = None
    if parsed_links["xml_url"]:
        raw_xml_path, xml_warning = fetch_and_store_xml(
            page.context, parsed_links["xml_url"], publication_id, publication_date, force
        )

    raw_content_json = json.dumps(
        {"headline": content.get("headline"), "field_values": content.get("field_values", [])},
        ensure_ascii=False,
    )

    data = {
        "publication_id": publication_id,
        "publication_number": first(metadata, "Publication number"),
        "publication_date": publication_date,
        "status": first(metadata, "Status"),
        "category": first(metadata, "Category"),
        "subcategory": first(metadata, "Subcategory"),
        "language": first(metadata, "Language"),
        "canton": first(metadata, "Canton"),
        "title": content.get("headline"),
        "company_name_raw": first(metadata, "Publishing entity"),
        "uid": parsed_links["uid"],
        "company_block_text": company_block_text,
        "body_text": body_text,
        "journal_number": journal_info["journal_number"],
        "journal_date": journal_info["journal_date"],
        "previous_sogc_number": journal_info["previous_sogc_number"],
        "previous_sogc_date": journal_info["previous_sogc_date"],
        "previous_publication_number": None,
        "contact_point": None,
        "detail_url": url,
        "xml_url": parsed_links["xml_url"],
        "pdf_url": parsed_links["pdf_url"],
        "zefix_url": parsed_links["zefix_url"],
        "raw_metadata_json": json.dumps(metadata, ensure_ascii=False),
        "raw_links_json": json.dumps(links, ensure_ascii=False),
        "raw_content_json": raw_content_json,
        "raw_content_html": content.get("html"),
        "raw_page_html_path": raw_page_html_path,
        "raw_xml_path": raw_xml_path,
        "content_hash": content_hash(content.get("html"), raw_content_json),
        "scraped_at": now_iso(),
    }

    db.upsert_publication_raw(conn, data)
    db.mark_queue_item_scraped(conn, publication_id)
    if xml_warning:
        conn.execute(
            "UPDATE publication_queue SET last_error = ? WHERE publication_id = ?",
            (xml_warning, publication_id),
        )
    conn.commit()
