from __future__ import annotations

import hashlib
import random
import re
import time
from datetime import date, datetime, timedelta, timezone

from . import config

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
UID_RE = re.compile(r"CHE-\d{3}\.\d{3}\.\d{3}")
PUBLICATION_NUMBER_RE = re.compile(r"HR\d{2}-\d+")
JOURNAL_RE = re.compile(
    r"Journal Number\s+(\d+)\s+from\s+(\d{2}\.\d{2}\.\d{4})"
)
PREVIOUS_PUBLICATION_RE = re.compile(
    r"Previous publication in the SOGC:\s*Number\s+(\d+),\s*Date:\s*(\d{2}\.\d{2}\.\d{4})"
)
DATE_IN_LIST_INFO_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def to_ddmmyyyy(iso_date: str) -> str:
    """Convert YYYY-MM-DD to dd.MM.yyyy."""
    d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return d.strftime("%d.%m.%Y")


def daterange(start_iso: str, end_iso: str):
    start = datetime.strptime(start_iso, "%Y-%m-%d").date()
    end = datetime.strptime(end_iso, "%Y-%m-%d").date()
    if start > end:
        raise ValueError("from-date must be <= to-date")
    current = start
    while current <= end:
        yield current.isoformat()
        current += timedelta(days=1)


def year_month(iso_date: str) -> tuple[str, str]:
    d = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return f"{d.year:04d}", f"{d.month:02d}"


def content_hash(*parts: str | None) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def random_pause(
    min_seconds: float = config.SCRAPE_PAUSE_MIN, max_seconds: float = config.SCRAPE_PAUSE_MAX
) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def extract_publication_number(list_info: str | None) -> str | None:
    if not list_info:
        return None
    m = PUBLICATION_NUMBER_RE.search(list_info)
    return m.group(0) if m else None


def extract_date_from_list_info(list_info: str | None) -> str | None:
    if not list_info:
        return None
    m = DATE_IN_LIST_INFO_RE.search(list_info)
    if not m:
        return None
    return datetime.strptime(m.group(0), "%d.%m.%Y").date().isoformat()


def extract_uid(*texts: str | None) -> str | None:
    for text in texts:
        if not text:
            continue
        m = UID_RE.search(text)
        if m:
            return m.group(0)
    return None
