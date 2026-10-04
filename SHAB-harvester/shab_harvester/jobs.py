"""Harvesting job logic, shared by the CLI (app.py) and the web UI's
background job runner (webui.py). Every function takes a `log` callback
instead of printing directly, so the same logic can stream into a CLI
terminal or into an in-memory job log shown in the browser.
"""
from __future__ import annotations

import random
import shutil
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import analysis
from . import browser as br
from . import config
from . import db
from .detail_scraper import DATA_DIR, RAW_HTML_DIR, RAW_XML_DIR, RateLimitError, scrape_publication_detail
from .discovery import discover_day as run_discover_day
from .utils import daterange, random_pause

MAX_CONSECUTIVE_RATE_LIMITS = config.MAX_CONSECUTIVE_RATE_LIMITS
EXPORT_DIR = DATA_DIR / "exports"


def init_db(log=print) -> None:
    db.init_db()
    log("Database initialized.")


def reset_all(
    confirm: bool,
    log=print,
    db_path: Path = db.DEFAULT_DB_PATH,
    raw_html_dir: Path = RAW_HTML_DIR,
    raw_xml_dir: Path = RAW_XML_DIR,
) -> None:
    """Wipe the database and all downloaded raw_html/raw_xml files, then
    recreate an empty schema. Irreversible — requires explicit confirmation."""
    if not confirm:
        log("Refusing to reset without confirmation. Pass --yes (CLI) or type RESET (web UI).")
        return

    if db_path.exists():
        db_path.unlink()
        log(f"Deleted {db_path}")

    for raw_dir in (raw_html_dir, raw_xml_dir):
        if raw_dir.exists():
            shutil.rmtree(raw_dir)
            log(f"Deleted {raw_dir}")
        raw_dir.mkdir(parents=True, exist_ok=True)

    db.init_db(db_path)
    log("Database re-initialized. Everything is back to a clean slate.")


def export_data(
    log=print,
    db_path: Path = db.DEFAULT_DB_PATH,
    raw_html_dir: Path = RAW_HTML_DIR,
    raw_xml_dir: Path = RAW_XML_DIR,
    export_dir: Path = EXPORT_DIR,
) -> Path:
    """Zip the sqlite DB + raw_html/raw_xml into one timestamped archive.
    Written to `export_dir`, which `reset_all`/`delete-all` never touch, so
    backups survive a wipe."""
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    zip_path = export_dir / f"shab_export_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if db_path.exists():
            zf.write(db_path, arcname="shab_harvester.sqlite")
            log(f"Added database ({db_path.stat().st_size} bytes).")
        else:
            log("No database file found — exporting raw files only.")

        for raw_dir, arc_prefix in ((raw_html_dir, "raw_html"), (raw_xml_dir, "raw_xml")):
            count = 0
            if raw_dir.exists():
                for file_path in raw_dir.rglob("*"):
                    if file_path.is_file():
                        zf.write(file_path, arcname=str(Path(arc_prefix) / file_path.relative_to(raw_dir)))
                        count += 1
            log(f"Added {count} file(s) from {arc_prefix}/.")

    log(f"Export written to {zip_path}")
    return zip_path


def list_exports(export_dir: Path = EXPORT_DIR) -> list[Path]:
    if not export_dir.exists():
        return []
    return sorted(export_dir.glob("shab_export_*.zip"), reverse=True)


def import_data(
    zip_path: Path,
    confirm: bool,
    log=print,
    db_path: Path = db.DEFAULT_DB_PATH,
    raw_html_dir: Path = RAW_HTML_DIR,
    raw_xml_dir: Path = RAW_XML_DIR,
) -> None:
    """Restore the DB + raw files from an export zip. Wipes whatever is
    currently there first (same as `reset_all`), then extracts. Irreversible
    — requires explicit confirmation."""
    if not confirm:
        log("Refusing to import without confirmation. Pass --yes (CLI) or type IMPORT (web UI).")
        return
    if not zip_path.exists():
        log(f"Zip file not found: {zip_path}")
        return

    reset_all(confirm=True, log=log, db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_dir)

        sqlite_src = tmp_dir / "shab_harvester.sqlite"
        if sqlite_src.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            if db_path.exists():
                db_path.unlink()
            shutil.move(str(sqlite_src), str(db_path))
            log("Restored database.")

        for raw_dir, arc_prefix in ((raw_html_dir, "raw_html"), (raw_xml_dir, "raw_xml")):
            src_dir = tmp_dir / arc_prefix
            if src_dir.exists():
                if raw_dir.exists():
                    shutil.rmtree(raw_dir)
                shutil.move(str(src_dir), str(raw_dir))
                log(f"Restored {arc_prefix}/.")
            else:
                raw_dir.mkdir(parents=True, exist_ok=True)

    log(f"Imported from {zip_path}")


def seed_days(from_date: str, to_date: str, log=print) -> None:
    with db.connect() as conn:
        days = list(daterange(from_date, to_date))
        for day in days:
            db.seed_day(conn, day)
    log(f"Seeded {len(days)} day(s) from {from_date} to {to_date}.")


def _discover_single_day(conn, publication_date: str, log) -> None:
    try:
        run_discover_day(conn, publication_date)
        row = db.get_import_day(conn, publication_date)
        status = row["status"] if row else "unknown"
        log(f"[discover] {publication_date}: {status}")
    except Exception as exc:
        db.mark_day_failed(conn, publication_date, str(exc))
        conn.commit()
        log(f"[discover] {publication_date}: FAILED ({exc})")


def discover_day(date: str, headless: bool, log=print) -> None:
    # `headless` stays in the signature for the CLI. Discovery reads the search API.
    _ = headless
    with db.connect() as conn:
        db.seed_day(conn, date)
        conn.commit()
        _discover_single_day(conn, date, log)


def discover_pending_days(headless: bool, log=print) -> None:
    _ = headless
    with db.connect() as conn:
        days = db.pending_or_failed_days(conn)
        if not days:
            log("No pending or failed days to discover.")
            return
        for row in days:
            _discover_single_day(conn, row["publication_date"], log)


def scrape_pending(limit: int, headless: bool, force: bool, log=print) -> None:
    with db.connect() as conn:
        reclaimed = db.reclaim_stale_running_queue_items(conn)
        if reclaimed:
            log(f"Reclaimed {reclaimed} item(s) stuck 'running' from a previous crashed run.")
        conn.commit()
        items = db.pending_queue_items(conn, limit)
        if not items:
            log("No pending or failed queue items to scrape.")
            return
        consecutive_rate_limits = 0
        with br.launch_browser(headless=headless) as browser, br.new_context(browser) as context:
            page = context.new_page()
            for index, item in enumerate(items):
                publication_id = item["publication_id"]
                db.mark_queue_item_running(conn, publication_id)
                conn.commit()
                try:
                    scrape_publication_detail(
                        conn,
                        page,
                        publication_id,
                        item["publication_date"],
                        item["detail_url"],
                        force=force,
                    )
                    db.update_day_scraped_count(conn, item["publication_date"])
                    conn.commit()
                    consecutive_rate_limits = 0
                    log(f"[scrape] {publication_id}: scraped")
                except RateLimitError as exc:
                    db.mark_queue_item_failed(conn, publication_id, str(exc), http_status=exc.status)
                    if db.maybe_archive_exhausted_failure(conn, publication_id):
                        log(f"[scrape] {publication_id}: archived as non_public (retries exhausted)")
                    conn.commit()
                    consecutive_rate_limits += 1
                    log(f"[scrape] {publication_id}: rate limited (HTTP {exc.status})")
                    if consecutive_rate_limits >= MAX_CONSECUTIVE_RATE_LIMITS:
                        log("Aborting run after repeated rate limiting.")
                        return
                    backoff = random.uniform(config.RATE_LIMIT_BACKOFF_MIN, config.RATE_LIMIT_BACKOFF_MAX)
                    log(f"Backing off for {backoff:.0f}s...")
                    time.sleep(backoff)
                except Exception as exc:
                    db.mark_queue_item_failed(conn, publication_id, str(exc))
                    if db.maybe_archive_exhausted_failure(conn, publication_id):
                        log(f"[scrape] {publication_id}: archived as non_public (retries exhausted)")
                    conn.commit()
                    log(f"[scrape] {publication_id}: FAILED ({exc})")

                if index < len(items) - 1:
                    random_pause()


def harvest_day(date: str, limit: int, headless: bool, force: bool, log=print) -> None:
    discover_day(date, headless, log)
    with db.connect() as conn:
        day = db.get_import_day(conn, date)
    if day and day["status"] in ("discovered", "completed"):
        scrape_pending(limit, headless, force, log)


def harvest_range(from_date: str, to_date: str, limit: int, headless: bool, force: bool, log=print) -> None:
    with db.connect() as conn:
        for day in daterange(from_date, to_date):
            db.seed_day(conn, day)
        conn.commit()
        with br.launch_browser(headless=headless) as browser, br.new_context(browser) as context:
            for day in daterange(from_date, to_date):
                row = db.get_import_day(conn, day)
                if row["status"] not in ("pending", "failed"):
                    log(f"[harvest] {day}: skipping discovery (status={row['status']})")
                else:
                    # Fresh page per day — see discover_pending_days for why.
                    page = context.new_page()
                    _discover_single_day(conn, page, day, log)
                    page.close()

    scrape_pending(limit, headless, force, log)


def reset_failed(log=print) -> None:
    with db.connect() as conn:
        queue_count = db.reset_failed_queue_items(conn)
        days_count = db.reset_failed_days(conn)
    log(f"Reset {queue_count} failed queue item(s) and {days_count} failed day(s) to pending.")


def archive_non_public(log=print) -> None:
    """Move exhausted failed queue items into shab_publication_non_public."""
    with db.connect() as conn:
        n = db.archive_exhausted_failures(conn)
        conn.commit()
    log(f"Archived {n} exhausted failure(s) as non_public.")


def analyze(limit: int | None, force: bool, log=print) -> None:
    with db.connect() as conn:
        processed = analysis.run_aggregate(conn, log=log, limit=limit, force=force)
    log(f"Analyzed {processed} publication(s).")
