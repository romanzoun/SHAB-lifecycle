from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config
from .utils import now_iso

DEFAULT_DB_PATH = config.DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS import_day (
    publication_date text PRIMARY KEY,
    status text NOT NULL DEFAULT 'pending',
    result_count integer,
    discovered_count integer DEFAULT 0,
    scraped_count integer DEFAULT 0,
    attempt_count integer DEFAULT 0,
    last_error text,
    started_at text,
    finished_at text,
    created_at text,
    updated_at text
);

CREATE TABLE IF NOT EXISTS publication_queue (
    publication_id text PRIMARY KEY,
    publication_date text NOT NULL,
    publication_number text,
    title text,
    list_info text,
    detail_url text,
    status text NOT NULL DEFAULT 'pending',
    attempt_count integer DEFAULT 0,
    http_status integer,
    last_error text,
    discovered_at text,
    scraped_at text,
    created_at text,
    updated_at text
);

CREATE TABLE IF NOT EXISTS shab_publication_raw (
    publication_id text PRIMARY KEY,
    publication_number text,
    publication_date text,
    status text,
    category text,
    subcategory text,
    language text,
    canton text,
    title text,
    company_name_raw text,
    uid text,
    company_block_text text,
    body_text text,
    journal_number text,
    journal_date text,
    previous_sogc_number text,
    previous_sogc_date text,
    previous_publication_number text,
    contact_point text,
    detail_url text,
    xml_url text,
    pdf_url text,
    zefix_url text,
    raw_metadata_json text,
    raw_links_json text,
    raw_content_json text,
    raw_content_html text,
    raw_page_html_path text,
    raw_xml_path text,
    content_hash text,
    scraped_at text,
    created_at text,
    updated_at text
);

CREATE INDEX IF NOT EXISTS idx_import_day_status ON import_day(status);
CREATE INDEX IF NOT EXISTS idx_publication_queue_status ON publication_queue(status);
CREATE INDEX IF NOT EXISTS idx_publication_queue_date ON publication_queue(publication_date);
CREATE INDEX IF NOT EXISTS idx_shab_publication_raw_uid ON shab_publication_raw(uid);
CREATE INDEX IF NOT EXISTS idx_shab_publication_raw_date ON shab_publication_raw(publication_date);
CREATE INDEX IF NOT EXISTS idx_shab_publication_raw_number ON shab_publication_raw(publication_number);

-- ---------------------------------------------------------------------------
-- Aggregation layer (second pass over shab_publication_raw, never mutates it).
-- Entity hierarchy: Organization -> Case -> Publication -> Person/Role.
-- Built by `analyze`; all heuristic (keyword/regex based), not authoritative.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS organizations (
    org_key text PRIMARY KEY,           -- 'uid:<UID>' or 'cand:<normalized name>|<canton>'
    uid text,                           -- NULL if no UID was ever observed
    match_confidence text NOT NULL,     -- 'HIGH' (uid) or 'LOW' (name/canton candidate)
    name_current text,
    legal_seat text,
    canton text,
    legal_form text,
    zefix_url text,
    first_seen_at text,
    last_seen_at text,
    publication_count integer DEFAULT 0,
    created_at text,
    updated_at text
);

CREATE TABLE IF NOT EXISTS organization_publications (
    org_key text NOT NULL,
    publication_id text NOT NULL,
    event_type text,
    event_date text,
    confidence text,
    created_at text,
    PRIMARY KEY (org_key, publication_id)
);

CREATE TABLE IF NOT EXISTS persons (
    person_key text PRIMARY KEY,        -- normalized_name|place, local key only, not a real identity
    full_name text,
    normalized_name text,
    place text,
    created_at text,
    updated_at text
);

CREATE TABLE IF NOT EXISTS person_roles (
    person_key text NOT NULL,
    org_key text,
    publication_id text NOT NULL,
    role text,
    signing_authority text,
    mutation_action text,               -- 'added' | 'removed' | 'unspecified'
    valid_from_publication_date text,
    created_at text,
    PRIMARY KEY (person_key, publication_id, org_key)
);

CREATE TABLE IF NOT EXISTS cases (
    case_id text PRIMARY KEY,           -- synthetic: '<org_key>:<case_type>'
    case_type text NOT NULL,
    org_key text,
    debtor_name text,
    office text,
    case_reference text,
    opened_date text,
    closed_date text,
    status text,
    created_at text,
    updated_at text
);

CREATE TABLE IF NOT EXISTS case_publications (
    case_id text NOT NULL,
    publication_id text NOT NULL,
    case_event_type text,
    event_date text,
    created_at text,
    PRIMARY KEY (case_id, publication_id)
);

CREATE TABLE IF NOT EXISTS aggregate_state (
    publication_id text PRIMARY KEY,
    content_hash text,
    processed_at text
);

-- Detail page unreachable after max scrape attempts: keep list-level evidence.
CREATE TABLE IF NOT EXISTS shab_publication_non_public (
    publication_id text PRIMARY KEY,
    publication_date text,
    publication_number text,
    title text,
    list_info text,
    detail_url text,
    rubric text,
    source_ref text,
    attempt_count integer,
    http_status integer,
    last_error text,
    availability text NOT NULL DEFAULT 'non_public',
    archived_at text NOT NULL,
    created_at text,
    updated_at text
);

CREATE INDEX IF NOT EXISTS idx_organizations_uid ON organizations(uid);
CREATE INDEX IF NOT EXISTS idx_org_publications_pub ON organization_publications(publication_id);
CREATE INDEX IF NOT EXISTS idx_person_roles_org ON person_roles(org_key);
CREATE INDEX IF NOT EXISTS idx_cases_org ON cases(org_key);
CREATE INDEX IF NOT EXISTS idx_non_public_date ON shab_publication_non_public(publication_date);
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL lets readers (status/status-detail/eta scripts) run concurrently
    # with the scraper's writes instead of hitting "database is locked" —
    # the default rollback-journal mode briefly gives writers an exclusive
    # lock that readers can collide with. WAL is sticky (stored in the
    # database file), so this only does real work once per file, but it's
    # cheap to re-assert on every connection and guarantees a fresh DB
    # created by init_db() gets it too. timeout=30 above is a second line of
    # defense: if a write is in progress, wait up to 30s and retry instead
    # of raising immediately.
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def connect(db_path: Path | str = DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# import_day
# ---------------------------------------------------------------------------

def seed_day(conn: sqlite3.Connection, publication_date: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO import_day (publication_date, status, created_at, updated_at)
        VALUES (?, 'pending', ?, ?)
        ON CONFLICT(publication_date) DO NOTHING
        """,
        (publication_date, ts, ts),
    )


def get_import_day(conn: sqlite3.Connection, publication_date: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM import_day WHERE publication_date = ?", (publication_date,)
    ).fetchone()


def mark_day_running(conn: sqlite3.Connection, publication_date: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE import_day
        SET status = 'running', started_at = ?, updated_at = ?,
            attempt_count = attempt_count + 1
        WHERE publication_date = ?
        """,
        (ts, ts, publication_date),
    )


def mark_day_empty(conn: sqlite3.Connection, publication_date: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE import_day
        SET status = 'empty', result_count = 0, discovered_count = 0,
            finished_at = ?, updated_at = ?, last_error = NULL
        WHERE publication_date = ?
        """,
        (ts, ts, publication_date),
    )


def mark_day_discovered(
    conn: sqlite3.Connection,
    publication_date: str,
    result_count: int,
    discovered_count: int,
    warning: str | None = None,
) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE import_day
        SET status = 'discovered', result_count = ?, discovered_count = ?,
            finished_at = ?, updated_at = ?, last_error = ?
        WHERE publication_date = ?
        """,
        (result_count, discovered_count, ts, ts, warning, publication_date),
    )


def mark_day_failed(conn: sqlite3.Connection, publication_date: str, error: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE import_day
        SET status = 'failed', last_error = ?, updated_at = ?
        WHERE publication_date = ?
        """,
        (error, ts, publication_date),
    )


def update_day_scraped_count(conn: sqlite3.Connection, publication_date: str) -> None:
    ts = now_iso()
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM publication_queue WHERE publication_date = ? AND status = 'scraped'",
        (publication_date,),
    ).fetchone()
    conn.execute(
        "UPDATE import_day SET scraped_count = ?, updated_at = ? WHERE publication_date = ?",
        (row["c"], ts, publication_date),
    )
    day = get_import_day(conn, publication_date)
    if day and day["status"] == "discovered" and day["result_count"] is not None:
        if row["c"] >= day["result_count"]:
            conn.execute(
                "UPDATE import_day SET status = 'completed', updated_at = ? WHERE publication_date = ?",
                (ts, publication_date),
            )


def pending_or_failed_days(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM import_day WHERE status IN ('pending', 'failed') ORDER BY publication_date"
    ).fetchall()


def all_import_days(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """import_day rows with live queue counts, for the dashboard overview."""
    return conn.execute(
        """
        SELECT
            d.*,
            COUNT(q.publication_id) AS queue_total,
            SUM(CASE WHEN q.status = 'scraped' THEN 1 ELSE 0 END) AS queue_scraped,
            SUM(CASE WHEN q.status = 'failed' THEN 1 ELSE 0 END) AS queue_failed,
            SUM(CASE WHEN q.status = 'pending' THEN 1 ELSE 0 END) AS queue_pending
        FROM import_day d
        LEFT JOIN publication_queue q ON q.publication_date = d.publication_date
        GROUP BY d.publication_date
        ORDER BY d.publication_date
        """
    ).fetchall()


# ---------------------------------------------------------------------------
# publication_queue
# ---------------------------------------------------------------------------

def upsert_queue_item(
    conn: sqlite3.Connection,
    publication_id: str,
    publication_date: str,
    publication_number: str | None,
    title: str | None,
    list_info: str | None,
    detail_url: str | None,
) -> None:
    ts = now_iso()
    existing = conn.execute(
        "SELECT * FROM publication_queue WHERE publication_id = ?", (publication_id,)
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO publication_queue (
                publication_id, publication_date, publication_number, title,
                list_info, detail_url, status, discovered_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
            """,
            (
                publication_id, publication_date, publication_number, title,
                list_info, detail_url, ts, ts, ts,
            ),
        )
    else:
        # Idempotent discovery: only fill in missing fields, never overwrite existing data.
        conn.execute(
            """
            UPDATE publication_queue
            SET publication_number = COALESCE(publication_number, ?),
                title = COALESCE(title, ?),
                list_info = COALESCE(list_info, ?),
                detail_url = COALESCE(detail_url, ?),
                updated_at = ?
            WHERE publication_id = ?
            """,
            (publication_number, title, list_info, detail_url, ts, publication_id),
        )


def pending_queue_items(
    conn: sqlite3.Connection, limit: int, max_attempts: int = config.MAX_QUEUE_ATTEMPTS
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM publication_queue
        WHERE status = 'pending'
           OR (status = 'failed' AND attempt_count < ?)
        ORDER BY publication_date, publication_id
        LIMIT ?
        """,
        (max_attempts, limit),
    ).fetchall()


def mark_queue_item_running(conn: sqlite3.Connection, publication_id: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE publication_queue
        SET status = 'running', attempt_count = attempt_count + 1, updated_at = ?
        WHERE publication_id = ?
        """,
        (ts, publication_id),
    )


def mark_queue_item_scraped(conn: sqlite3.Connection, publication_id: str) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE publication_queue
        SET status = 'scraped', scraped_at = ?, updated_at = ?, last_error = NULL
        WHERE publication_id = ?
        """,
        (ts, ts, publication_id),
    )


def mark_queue_item_failed(
    conn: sqlite3.Connection, publication_id: str, error: str, http_status: int | None = None
) -> None:
    ts = now_iso()
    conn.execute(
        """
        UPDATE publication_queue
        SET status = 'failed', last_error = ?, http_status = COALESCE(?, http_status), updated_at = ?
        WHERE publication_id = ?
        """,
        (error, http_status, ts, publication_id),
    )


def _parse_list_info_hints(list_info: str | None) -> tuple[str | None, str | None]:
    """Best-effort parse of discovery list_info into (source_ref, rubric).

    Typical: '02.07.2021 - KK02-0000019796 - SOGC, Official Gazette ZH - Bankruptcies'
    """
    if not list_info:
        return None, None
    parts = [p.strip() for p in list_info.split(" - ") if p.strip()]
    source_ref = parts[1] if len(parts) >= 2 else None
    rubric = parts[-1] if parts else None
    return source_ref, rubric


def upsert_non_public_from_queue_row(conn: sqlite3.Connection, row: sqlite3.Row) -> None:
    """Persist list-level evidence when a detail page is no longer public."""
    ts = now_iso()
    source_ref, rubric = _parse_list_info_hints(row["list_info"] if "list_info" in row.keys() else None)
    conn.execute(
        """
        INSERT INTO shab_publication_non_public (
            publication_id, publication_date, publication_number, title, list_info,
            detail_url, rubric, source_ref, attempt_count, http_status, last_error,
            availability, archived_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'non_public', ?, ?, ?)
        ON CONFLICT(publication_id) DO UPDATE SET
            publication_date = excluded.publication_date,
            publication_number = COALESCE(excluded.publication_number, shab_publication_non_public.publication_number),
            title = COALESCE(excluded.title, shab_publication_non_public.title),
            list_info = COALESCE(excluded.list_info, shab_publication_non_public.list_info),
            detail_url = COALESCE(excluded.detail_url, shab_publication_non_public.detail_url),
            rubric = COALESCE(excluded.rubric, shab_publication_non_public.rubric),
            source_ref = COALESCE(excluded.source_ref, shab_publication_non_public.source_ref),
            attempt_count = excluded.attempt_count,
            http_status = COALESCE(excluded.http_status, shab_publication_non_public.http_status),
            last_error = excluded.last_error,
            archived_at = excluded.archived_at,
            updated_at = excluded.updated_at
        """,
        (
            row["publication_id"],
            row["publication_date"],
            row["publication_number"] if "publication_number" in row.keys() else None,
            row["title"],
            row["list_info"] if "list_info" in row.keys() else None,
            row["detail_url"],
            rubric,
            source_ref,
            row["attempt_count"],
            row["http_status"] if "http_status" in row.keys() else None,
            row["last_error"] if "last_error" in row.keys() else None,
            ts,
            ts,
            ts,
        ),
    )
    conn.execute(
        """
        UPDATE publication_queue
        SET status = 'non_public', updated_at = ?
        WHERE publication_id = ?
        """,
        (ts, row["publication_id"]),
    )


def maybe_archive_exhausted_failure(
    conn: sqlite3.Connection,
    publication_id: str,
    max_attempts: int = config.MAX_QUEUE_ATTEMPTS,
) -> bool:
    """If failed attempts are exhausted, copy list evidence into non_public."""
    row = conn.execute(
        "SELECT * FROM publication_queue WHERE publication_id = ?", (publication_id,)
    ).fetchone()
    if row is None or row["status"] != "failed":
        return False
    if row["attempt_count"] < max_attempts:
        return False
    upsert_non_public_from_queue_row(conn, row)
    return True


def archive_exhausted_failures(
    conn: sqlite3.Connection, max_attempts: int = config.MAX_QUEUE_ATTEMPTS
) -> int:
    """Archive all failed queue rows that have exhausted retries."""
    rows = conn.execute(
        """
        SELECT * FROM publication_queue
        WHERE status = 'failed' AND attempt_count >= ?
        ORDER BY publication_date, publication_id
        """,
        (max_attempts,),
    ).fetchall()
    for row in rows:
        upsert_non_public_from_queue_row(conn, row)
    return len(rows)


def reset_failed_queue_items(conn: sqlite3.Connection) -> int:
    # 'running' is included alongside 'failed': a row stuck there means the
    # process died mid-scrape without marking it failed, so it's invisible
    # to pending_queue_items() and would otherwise never be retried.
    cur = conn.execute(
        "UPDATE publication_queue SET status = 'pending', updated_at = ? WHERE status IN ('failed', 'running')",
        (now_iso(),),
    )
    return cur.rowcount


def reclaim_stale_running_queue_items(conn: sqlite3.Connection) -> int:
    """Resets 'running' queue items back to 'pending' at the start of a
    scrape run. In the current single-worker model, a 'running' row can
    only mean a previous process died mid-item (no sibling worker could be
    holding it) — so it's always safe to reclaim here. Would need removing
    if/when true parallel workers are introduced."""
    cur = conn.execute(
        "UPDATE publication_queue SET status = 'pending', updated_at = ? WHERE status = 'running'",
        (now_iso(),),
    )
    return cur.rowcount


def reset_failed_days(conn: sqlite3.Connection) -> int:
    # Same reasoning as reset_failed_queue_items: a day stuck in 'running'
    # means discover_day was interrupted before recording empty/discovered.
    cur = conn.execute(
        "UPDATE import_day SET status = 'pending', updated_at = ? WHERE status IN ('failed', 'running')",
        (now_iso(),),
    )
    return cur.rowcount


def repair_queue_status(conn: sqlite3.Connection) -> int:
    """If shab_publication_raw exists but queue item is not 'scraped', fix it."""
    cur = conn.execute(
        """
        UPDATE publication_queue
        SET status = 'scraped', scraped_at = COALESCE(scraped_at, ?), updated_at = ?
        WHERE status != 'scraped'
          AND publication_id IN (SELECT publication_id FROM shab_publication_raw)
        """,
        (now_iso(), now_iso()),
    )
    return cur.rowcount


# ---------------------------------------------------------------------------
# shab_publication_raw
# ---------------------------------------------------------------------------

def upsert_publication_raw(conn: sqlite3.Connection, data: dict) -> None:
    ts = now_iso()
    existing = conn.execute(
        "SELECT publication_id FROM shab_publication_raw WHERE publication_id = ?",
        (data["publication_id"],),
    ).fetchone()
    data = dict(data)
    data["updated_at"] = ts
    if existing is None:
        data["created_at"] = ts
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        conn.execute(
            f"INSERT INTO shab_publication_raw ({', '.join(columns)}) VALUES ({placeholders})",
            [data[c] for c in columns],
        )
    else:
        columns = [c for c in data.keys() if c != "publication_id"]
        set_clause = ", ".join(f"{c} = ?" for c in columns)
        conn.execute(
            f"UPDATE shab_publication_raw SET {set_clause} WHERE publication_id = ?",
            [data[c] for c in columns] + [data["publication_id"]],
        )


# ---------------------------------------------------------------------------
# status / verify helpers
# ---------------------------------------------------------------------------

def counts_by_status(conn: sqlite3.Connection, table: str) -> dict[str, int]:
    rows = conn.execute(f"SELECT status, COUNT(*) AS c FROM {table} GROUP BY status").fetchall()
    return {row["status"]: row["c"] for row in rows}


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def failed_queue_items(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT publication_id, publication_date, attempt_count, last_error FROM publication_queue "
        "WHERE status = 'failed' ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()


def day_overview(
    conn: sqlite3.Connection, publication_date: str, status: str | None = None
) -> list[sqlite3.Row]:
    """One row per known shab-id (publication_id) for a day, with its current
    state-machine status (pending/running/scraped/failed) and whether the raw
    detail row has actually landed in shab_publication_raw."""
    sql = """
        SELECT
            q.publication_id,
            q.publication_number,
            q.title,
            q.status,
            q.attempt_count,
            q.last_error,
            q.discovered_at,
            q.scraped_at,
            (r.publication_id IS NOT NULL) AS has_raw
        FROM publication_queue q
        LEFT JOIN shab_publication_raw r ON r.publication_id = q.publication_id
        WHERE q.publication_date = ?
    """
    params: list = [publication_date]
    if status:
        sql += " AND q.status = ?"
        params.append(status)
    sql += " ORDER BY q.publication_number, q.publication_id"
    return conn.execute(sql, params).fetchall()


def get_queue_item(conn: sqlite3.Connection, publication_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM publication_queue WHERE publication_id = ?", (publication_id,)
    ).fetchone()


def get_publication_raw(conn: sqlite3.Connection, publication_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM shab_publication_raw WHERE publication_id = ?", (publication_id,)
    ).fetchone()


def all_publication_raw(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM shab_publication_raw ORDER BY publication_date").fetchall()


# ---------------------------------------------------------------------------
# Aggregation layer: organizations / persons / cases (built by analysis.py)
# ---------------------------------------------------------------------------

def pending_aggregate_publications(conn: sqlite3.Connection, limit: int | None, force: bool) -> list[sqlite3.Row]:
    if force:
        sql = "SELECT * FROM shab_publication_raw ORDER BY publication_date"
        params: tuple = ()
    else:
        sql = """
            SELECT r.* FROM shab_publication_raw r
            LEFT JOIN aggregate_state s ON s.publication_id = r.publication_id
            WHERE s.publication_id IS NULL OR s.content_hash IS NOT r.content_hash
            ORDER BY r.publication_date
        """
        params = ()
    if limit:
        sql += " LIMIT ?"
        params = (*params, limit)
    return conn.execute(sql, params).fetchall()


def mark_aggregate_processed(conn: sqlite3.Connection, publication_id: str, content_hash: str | None) -> None:
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO aggregate_state (publication_id, content_hash, processed_at)
        VALUES (?, ?, ?)
        ON CONFLICT(publication_id) DO UPDATE SET content_hash = ?, processed_at = ?
        """,
        (publication_id, content_hash, ts, content_hash, ts),
    )


def upsert_organization(conn: sqlite3.Connection, org: dict) -> None:
    ts = now_iso()
    existing = conn.execute(
        "SELECT * FROM organizations WHERE org_key = ?", (org["org_key"],)
    ).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO organizations (
                org_key, uid, match_confidence, name_current, legal_seat, canton,
                legal_form, zefix_url, first_seen_at, last_seen_at, publication_count,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                org["org_key"], org.get("uid"), org["match_confidence"], org.get("name_current"),
                org.get("legal_seat"), org.get("canton"), org.get("legal_form"), org.get("zefix_url"),
                org.get("event_date") or ts, org.get("event_date") or ts, ts, ts,
            ),
        )
    else:
        first_seen = existing["first_seen_at"]
        last_seen = existing["last_seen_at"]
        candidate_date = org.get("event_date")
        if candidate_date:
            if not first_seen or candidate_date < first_seen:
                first_seen = candidate_date
            if not last_seen or candidate_date > last_seen:
                last_seen = candidate_date
        conn.execute(
            """
            UPDATE organizations
            SET uid = COALESCE(?, uid),
                name_current = COALESCE(?, name_current),
                legal_seat = COALESCE(?, legal_seat),
                canton = COALESCE(?, canton),
                legal_form = COALESCE(?, legal_form),
                zefix_url = COALESCE(?, zefix_url),
                first_seen_at = ?,
                last_seen_at = ?,
                updated_at = ?
            WHERE org_key = ?
            """,
            (
                org.get("uid"), org.get("name_current"), org.get("legal_seat"), org.get("canton"),
                org.get("legal_form"), org.get("zefix_url"), first_seen, last_seen, ts, org["org_key"],
            ),
        )


def recompute_organization_publication_count(conn: sqlite3.Connection, org_key: str) -> None:
    count = scalar(
        conn, "SELECT COUNT(*) FROM organization_publications WHERE org_key = ?", (org_key,)
    )
    conn.execute(
        "UPDATE organizations SET publication_count = ?, updated_at = ? WHERE org_key = ?",
        (count, now_iso(), org_key),
    )


def upsert_organization_publication(
    conn: sqlite3.Connection, org_key: str, publication_id: str, event_type: str | None,
    event_date: str | None, confidence: str,
) -> None:
    conn.execute(
        """
        INSERT INTO organization_publications (org_key, publication_id, event_type, event_date, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(org_key, publication_id) DO UPDATE SET
            event_type = ?, event_date = ?, confidence = ?
        """,
        (org_key, publication_id, event_type, event_date, confidence, now_iso(), event_type, event_date, confidence),
    )


def delete_publication_aggregates(conn: sqlite3.Connection, publication_id: str) -> None:
    """Remove everything derived from this publication, so re-running `analyze` is idempotent."""
    conn.execute("DELETE FROM organization_publications WHERE publication_id = ?", (publication_id,))
    conn.execute("DELETE FROM person_roles WHERE publication_id = ?", (publication_id,))
    conn.execute("DELETE FROM case_publications WHERE publication_id = ?", (publication_id,))


def reset_aggregates(conn: sqlite3.Connection) -> None:
    """Full wipe of the aggregate layer. `organizations`/`cases` are merged
    additively across publications (COALESCE), so a heuristic change only
    takes full effect on already-aggregated entities if they're rebuilt
    from scratch — this is what `analyze --force` triggers."""
    for table in (
        "organization_publications", "person_roles", "case_publications",
        "organizations", "persons", "cases", "aggregate_state",
    ):
        conn.execute(f"DELETE FROM {table}")


def upsert_person(conn: sqlite3.Connection, person_key: str, full_name: str, normalized_name: str, place: str | None) -> None:
    ts = now_iso()
    conn.execute(
        """
        INSERT INTO persons (person_key, full_name, normalized_name, place, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(person_key) DO UPDATE SET full_name = ?, normalized_name = ?, place = ?, updated_at = ?
        """,
        (person_key, full_name, normalized_name, place, ts, ts, full_name, normalized_name, place, ts),
    )


def insert_person_role(
    conn: sqlite3.Connection, person_key: str, org_key: str | None, publication_id: str,
    role: str | None, signing_authority: str | None, mutation_action: str | None,
    valid_from_publication_date: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO person_roles (
            person_key, org_key, publication_id, role, signing_authority,
            mutation_action, valid_from_publication_date, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(person_key, publication_id, org_key) DO UPDATE SET
            role = ?, signing_authority = ?, mutation_action = ?, valid_from_publication_date = ?
        """,
        (
            person_key, org_key, publication_id, role, signing_authority, mutation_action,
            valid_from_publication_date, now_iso(), role, signing_authority, mutation_action,
            valid_from_publication_date,
        ),
    )


def upsert_case(conn: sqlite3.Connection, case: dict) -> None:
    ts = now_iso()
    existing = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case["case_id"],)).fetchone()
    if existing is None:
        conn.execute(
            """
            INSERT INTO cases (
                case_id, case_type, org_key, debtor_name, office, case_reference,
                opened_date, closed_date, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case["case_id"], case["case_type"], case.get("org_key"), case.get("debtor_name"),
                case.get("office"), case.get("case_reference"), case.get("opened_date"),
                case.get("closed_date"), case.get("status"), ts, ts,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE cases
            SET office = COALESCE(?, office),
                case_reference = COALESCE(?, case_reference),
                opened_date = COALESCE(opened_date, ?),
                closed_date = COALESCE(?, closed_date),
                status = COALESCE(?, status),
                updated_at = ?
            WHERE case_id = ?
            """,
            (
                case.get("office"), case.get("case_reference"), case.get("opened_date"),
                case.get("closed_date"), case.get("status"), ts, case["case_id"],
            ),
        )


def insert_case_publication(
    conn: sqlite3.Connection, case_id: str, publication_id: str, case_event_type: str | None, event_date: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO case_publications (case_id, publication_id, case_event_type, event_date, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(case_id, publication_id) DO UPDATE SET case_event_type = ?, event_date = ?
        """,
        (case_id, publication_id, case_event_type, event_date, now_iso(), case_event_type, event_date),
    )


def list_organizations(conn: sqlite3.Connection, search: str | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM organizations"
    params: tuple = ()
    if search:
        sql += " WHERE name_current LIKE ? OR uid LIKE ? OR org_key LIKE ?"
        like = f"%{search}%"
        params = (like, like, like)
    sql += " ORDER BY publication_count DESC, name_current"
    return conn.execute(sql, params).fetchall()


def get_organization(conn: sqlite3.Connection, org_key: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM organizations WHERE org_key = ?", (org_key,)).fetchone()


def organization_publication_rows(conn: sqlite3.Connection, org_key: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT op.*, r.title, r.publication_date, r.category, r.subcategory
        FROM organization_publications op
        JOIN shab_publication_raw r ON r.publication_id = op.publication_id
        WHERE op.org_key = ?
        ORDER BY r.publication_date
        """,
        (org_key,),
    ).fetchall()


def organization_persons(conn: sqlite3.Connection, org_key: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT pr.*, p.full_name, p.place
        FROM person_roles pr
        JOIN persons p ON p.person_key = pr.person_key
        WHERE pr.org_key = ?
        ORDER BY pr.valid_from_publication_date
        """,
        (org_key,),
    ).fetchall()


def organization_cases(conn: sqlite3.Connection, org_key: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM cases WHERE org_key = ? ORDER BY opened_date", (org_key,)).fetchall()


def list_cases(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM cases ORDER BY opened_date DESC").fetchall()


def get_case(conn: sqlite3.Connection, case_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,)).fetchone()


def case_publication_rows(conn: sqlite3.Connection, case_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT cp.*, r.title, r.publication_date
        FROM case_publications cp
        JOIN shab_publication_raw r ON r.publication_id = cp.publication_id
        WHERE cp.case_id = ?
        ORDER BY r.publication_date
        """,
        (case_id,),
    ).fetchall()


def aggregate_counts(conn: sqlite3.Connection) -> dict:
    return {
        "organizations": scalar(conn, "SELECT COUNT(*) FROM organizations"),
        "organizations_with_uid": scalar(conn, "SELECT COUNT(*) FROM organizations WHERE uid IS NOT NULL"),
        "persons": scalar(conn, "SELECT COUNT(*) FROM persons"),
        "cases": scalar(conn, "SELECT COUNT(*) FROM cases"),
        "cases_open": scalar(conn, "SELECT COUNT(*) FROM cases WHERE status = 'open'"),
        "processed_publications": scalar(conn, "SELECT COUNT(*) FROM aggregate_state"),
    }
