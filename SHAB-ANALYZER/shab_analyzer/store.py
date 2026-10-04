from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Event, ParseResult
from .utils_iso import now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS parse_run (
    publication_id text PRIMARY KEY,
    published_at text,
    language text,
    sub_rubric text,
    org_uid text,
    canton text,
    plz text,
    status text,
    leftover_text text,
    parsed_at text
);
CREATE TABLE IF NOT EXISTS analyzer_event (
    id integer PRIMARY KEY AUTOINCREMENT,
    publication_id text NOT NULL,
    published_at text,
    event_type text NOT NULL,
    rule_id text,
    org_uid text,
    person_key text,
    plz text,
    canton text,
    role text,
    signing text,
    payload_json text
);
CREATE INDEX IF NOT EXISTS idx_ae_pub ON analyzer_event(publication_id);
CREATE INDEX IF NOT EXISTS idx_ae_person ON analyzer_event(person_key, published_at);
CREATE INDEX IF NOT EXISTS idx_ae_plz ON analyzer_event(plz, published_at);
CREATE INDEX IF NOT EXISTS idx_ae_org ON analyzer_event(org_uid, published_at);
CREATE TABLE IF NOT EXISTS walk_job (
    id integer PRIMARY KEY CHECK (id = 1),
    state text NOT NULL,
    parser_version integer NOT NULL,
    discover_cursor text,
    pid integer,
    heartbeat_at text,
    started_at text,
    last_error text,
    processed integer NOT NULL DEFAULT 0,
    ok_count integer NOT NULL DEFAULT 0,
    partial_count integer NOT NULL DEFAULT 0,
    deferred_count integer NOT NULL DEFAULT 0,
    error_count integer NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS walk_item (
    relpath text PRIMARY KEY,
    publication_id text,
    status text NOT NULL,
    parser_version integer,
    error_text text,
    updated_at text
);
CREATE INDEX IF NOT EXISTS idx_walk_item_status ON walk_item(status, relpath);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(parse_run)")}
    if "parser_version" not in cols:
        conn.execute("ALTER TABLE parse_run ADD COLUMN parser_version integer")
    if "source_relpath" not in cols:
        conn.execute("ALTER TABLE parse_run ADD COLUMN source_relpath text")
    if "error_text" not in cols:
        conn.execute("ALTER TABLE parse_run ADD COLUMN error_text text")
    job_cols = {row[1] for row in conn.execute("PRAGMA table_info(walk_job)")}
    if "unlocked_rubrics" not in job_cols:
        conn.execute("ALTER TABLE walk_job ADD COLUMN unlocked_rubrics text")
        conn.execute("UPDATE walk_job SET unlocked_rubrics = 'HR' WHERE id = 1")
    conn.commit()


def replace_parse(
    conn: sqlite3.Connection,
    result: ParseResult,
    *,
    parser_version: int | None = None,
    source_relpath: str | None = None,
    error_text: str | None = None,
    commit: bool = True,
) -> None:
    conn.execute("DELETE FROM analyzer_event WHERE publication_id = ?", (result.publication_id,))
    conn.execute(
        """
        INSERT INTO parse_run (
            publication_id, published_at, language, sub_rubric, org_uid, canton, plz,
            status, leftover_text, parsed_at, parser_version, source_relpath, error_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(publication_id) DO UPDATE SET
            published_at=excluded.published_at,
            language=excluded.language,
            sub_rubric=excluded.sub_rubric,
            org_uid=excluded.org_uid,
            canton=excluded.canton,
            plz=excluded.plz,
            status=excluded.status,
            leftover_text=excluded.leftover_text,
            parsed_at=excluded.parsed_at,
            parser_version=excluded.parser_version,
            source_relpath=excluded.source_relpath,
            error_text=excluded.error_text
        """,
        (
            result.publication_id,
            result.published_at,
            result.language,
            result.sub_rubric,
            result.org_uid,
            result.canton,
            result.plz,
            result.status,
            result.leftover_text,
            now_iso(),
            parser_version,
            source_relpath,
            error_text,
        ),
    )
    for event in result.events:
        insert_event(conn, event)
    if commit:
        conn.commit()


def insert_event(conn: sqlite3.Connection, event: Event) -> None:
    conn.execute(
        """
        INSERT INTO analyzer_event (
            publication_id, published_at, event_type, rule_id, org_uid, person_key,
            plz, canton, role, signing, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.publication_id,
            event.published_at,
            event.event_type,
            event.rule_id,
            event.org_uid,
            event.person_key,
            event.plz,
            event.canton,
            event.role,
            event.signing,
            json.dumps(event.payload, ensure_ascii=False),
        ),
    )


def all_events(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM analyzer_event ORDER BY published_at, id").fetchall()
