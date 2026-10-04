"""Durable walk state machine over harvest XML.

States (walk_job.state):
  idle         — no work in flight
  discovering  — inserting paths from the raw XML tree
  walking      — parsing pending items
  complete     — current parser_version has no pending items
  failed       — uncaught error; resume re-enters walking/discovering

Crash recovery: a RUNNING/DISCOVERING job with a dead pid is taken over.
Pending items stay pending (batch commit). FULLY_PARSED items stay done.
PARTIAL/ERROR are re-queued when PARSER_VERSION increases.
"""

from __future__ import annotations

import fcntl
import os
import time
from pathlib import Path

from . import config
from . import store
from .models import ParseResult
from .parse import parse_publication_xml
from .utils_iso import now_iso

STATES = ("idle", "discovering", "walking", "complete", "failed")
STALE_SECONDS = 120
BATCH_SIZE = 200


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock(lock_path: Path):
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    handle.write(f"{os.getpid()} {now_iso()}\n")
    handle.flush()
    return handle


def ensure_job(conn) -> None:
    row = conn.execute("SELECT id FROM walk_job WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            """
            INSERT INTO walk_job (
                id, state, parser_version, processed,
                ok_count, partial_count, deferred_count, error_count,
                unlocked_rubrics
            ) VALUES (1, 'idle', 0, 0, 0, 0, 0, 0, 'HR')
            """
        )
        conn.commit()


def job_row(conn):
    ensure_job(conn)
    return conn.execute("SELECT * FROM walk_job WHERE id = 1").fetchone()


def _set_state(conn, state: str, **fields) -> None:
    assignments = ["state = ?", "heartbeat_at = ?"]
    values: list = [state, now_iso()]
    for key, value in fields.items():
        assignments.append(f"{key} = ?")
        values.append(value)
    values.append(1)
    conn.execute(f"UPDATE walk_job SET {', '.join(assignments)} WHERE id = ?", values)


def recover_if_stale(conn) -> str | None:
    job = job_row(conn)
    state = job["state"]
    if state not in ("discovering", "walking"):
        return None
    heartbeat = job["heartbeat_at"] or ""
    stale = True
    if heartbeat:
        # Compare as ISO-Z strings is enough for crash takeover; pid is the source of truth.
        stale = not _pid_alive(job["pid"])
    if not stale:
        if job["pid"] and int(job["pid"]) != os.getpid():
            return "owned"
        return None
    _set_state(
        conn,
        state,
        pid=os.getpid(),
        last_error=f"recovered stale pid={job['pid']}",
        started_at=job["started_at"] or now_iso(),
    )
    conn.commit()
    return "recovered"


def requeue_stale_rules(conn, parser_version: int) -> int:
    cur = conn.execute(
        """
        UPDATE walk_item
        SET status = 'pending', error_text = NULL, updated_at = ?
        WHERE parser_version IS NOT NULL
          AND parser_version < ?
          AND status IN ('partial', 'error')
        """,
        (now_iso(), parser_version),
    )
    conn.execute("UPDATE walk_job SET parser_version = ? WHERE id = 1", (parser_version,))
    conn.commit()
    return cur.rowcount


def unlocked_rubric_prefixes(conn) -> tuple[str, ...]:
    job = job_row(conn)
    raw = "HR"
    try:
        raw = job["unlocked_rubrics"] or "HR"
    except (KeyError, IndexError):
        pass
    prefixes = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    return prefixes or ("HR",)


def unlock_deferred_family(conn, family: str) -> int:
    family = family.strip().upper()
    prefixes = list(unlocked_rubric_prefixes(conn))
    if family not in prefixes:
        prefixes.append(family)
        conn.execute(
            "UPDATE walk_job SET unlocked_rubrics = ? WHERE id = 1",
            (",".join(prefixes),),
        )
    cur = conn.execute(
        """
        UPDATE walk_item
        SET status = 'pending', error_text = NULL, updated_at = ?
        WHERE status = 'deferred'
          AND publication_id IN (
            SELECT publication_id FROM parse_run WHERE sub_rubric LIKE ?
          )
        """,
        (now_iso(), f"{family}%"),
    )
    conn.commit()
    return int(cur.rowcount)


def _month_buckets(xml_root: Path) -> list[tuple[str, Path]]:
    year_dirs = sorted(p for p in xml_root.iterdir() if p.is_dir() and p.name.isdigit())
    if not year_dirs:
        return [("", xml_root)]
    buckets = []
    for year in year_dirs:
        months = sorted(p for p in year.iterdir() if p.is_dir())
        if not months:
            continue
        for month in months:
            buckets.append((f"{year.name}/{month.name}", month))
    return buckets


def discover(conn, xml_root: Path, *, resume: bool = False, after_month=None) -> int:
    xml_root = xml_root.resolve()
    job = job_row(conn)
    cursor = (job["discover_cursor"] or "") if resume else ""
    _set_state(conn, "discovering", pid=os.getpid(), parser_version=config.PARSER_VERSION)
    conn.commit()
    inserted = 0
    for key, folder in _month_buckets(xml_root):
        if key and key < cursor:
            continue
        rows = []
        for xml in sorted(folder.glob("*.xml")):
            rel = f"{key}/{xml.name}" if key else xml.name
            rows.append((rel, xml.stem, "pending", now_iso()))
        if rows:
            conn.executemany(
                """
                INSERT OR IGNORE INTO walk_item (relpath, publication_id, status, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                rows,
            )
            inserted += len(rows)
        if key:
            conn.execute(
                "UPDATE walk_job SET discover_cursor = ?, heartbeat_at = ? WHERE id = 1",
                (key, now_iso()),
            )
        conn.commit()
        if after_month is not None:
            after_month()
    return inserted


def _item_status(result: ParseResult, prefixes: tuple[str, ...] = ("HR",)) -> str:
    rubric = result.sub_rubric or ""
    if rubric and not any(rubric.startswith(prefix) for prefix in prefixes):
        return "deferred"
    if result.status == "FULLY_PARSED":
        return "ok"
    if result.status == "ERROR":
        return "error"
    return "partial"


def _error_result(publication_id: str, exc: BaseException) -> ParseResult:
    return ParseResult(
        publication_id=publication_id,
        published_at="",
        language=None,
        sub_rubric=None,
        org_uid=None,
        canton=None,
        plz=None,
        events=[],
        leftover_text=repr(exc),
        status="ERROR",
    )


def _bump_counters(conn, item_status: str) -> None:
    column = {
        "ok": "ok_count",
        "partial": "partial_count",
        "deferred": "deferred_count",
        "error": "error_count",
    }[item_status]
    conn.execute(
        f"UPDATE walk_job SET processed = processed + 1, {column} = {column} + 1, heartbeat_at = ? WHERE id = 1",
        (now_iso(),),
    )


def process_batch(conn, xml_root: Path, batch_size: int = BATCH_SIZE) -> int:
    xml_root = xml_root.resolve()
    rows = conn.execute(
        "SELECT relpath, publication_id FROM walk_item WHERE status = 'pending' ORDER BY relpath LIMIT ?",
        (batch_size,),
    ).fetchall()
    if not rows:
        return 0
    _set_state(conn, "walking", pid=os.getpid(), parser_version=config.PARSER_VERSION)
    conn.commit()
    done = 0
    for row in rows:
        relpath = row["relpath"]
        pub_id = row["publication_id"] or Path(relpath).stem
        path = xml_root / relpath
        try:
            result = parse_publication_xml(path, publication_id=pub_id)
        except Exception as exc:  # noqa: BLE001 — walk must continue
            result = _error_result(pub_id, exc)
        item_status = _item_status(result, unlocked_rubric_prefixes(conn))
        store.replace_parse(
            conn,
            result,
            parser_version=config.PARSER_VERSION,
            source_relpath=relpath,
            error_text=result.leftover_text if result.status == "ERROR" else None,
            commit=False,
        )
        conn.execute(
            """
            UPDATE walk_item
            SET status = ?, parser_version = ?, error_text = ?, publication_id = ?, updated_at = ?
            WHERE relpath = ?
            """,
            (
                item_status,
                config.PARSER_VERSION,
                result.leftover_text if item_status == "error" else None,
                result.publication_id,
                now_iso(),
                relpath,
            ),
        )
        _bump_counters(conn, item_status)
        done += 1
        if done % 50 == 0:
            conn.commit()
    conn.commit()
    return done


def pending_count(conn) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM walk_item WHERE status = 'pending'").fetchone()
    return int(row["n"])


def coverage(conn) -> dict:
    ensure_job(conn)
    job = job_row(conn)
    counts = {row["status"]: row["n"] for row in conn.execute(
        "SELECT status, COUNT(*) AS n FROM walk_item GROUP BY status"
    )}
    parse_counts = {row["status"]: row["n"] for row in conn.execute(
        "SELECT status, COUNT(*) AS n FROM parse_run GROUP BY status"
    )}
    return {
        "job_state": job["state"],
        "parser_version": job["parser_version"],
        "pid": job["pid"],
        "heartbeat_at": job["heartbeat_at"],
        "discover_cursor": job["discover_cursor"],
        "last_error": job["last_error"],
        "unlocked_rubrics": (job["unlocked_rubrics"] if "unlocked_rubrics" in job.keys() else None) or "HR",
        "job_counters": {
            "processed": job["processed"],
            "ok": job["ok_count"],
            "partial": job["partial_count"],
            "deferred": job["deferred_count"],
            "error": job["error_count"],
        },
        "items": counts,
        "parse_run": parse_counts,
        "pending": counts.get("pending", 0),
    }


def gap_samples(conn, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """
        SELECT language, sub_rubric, status, leftover_text, COUNT(*) AS n
        FROM parse_run
        WHERE status IN ('PARTIALLY_PARSED', 'ERROR')
        GROUP BY language, sub_rubric, status, leftover_text
        ORDER BY n DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "language": row["language"],
            "sub_rubric": row["sub_rubric"],
            "status": row["status"],
            "count": row["n"],
            "leftover": (row["leftover_text"] or "")[:240],
        }
        for row in rows
    ]


def tick(conn, xml_root: Path, batch_size: int = BATCH_SIZE, limit: int | None = None) -> int:
    recovered = recover_if_stale(conn)
    if recovered == "owned":
        return 0
    job = job_row(conn)
    if job["state"] == "failed":
        _set_state(conn, "walking", pid=os.getpid(), started_at=job["started_at"] or now_iso())
        conn.commit()
    requeue_stale_rules(conn, config.PARSER_VERSION)
    job = job_row(conn)
    if not job["started_at"]:
        _set_state(conn, "discovering", started_at=now_iso(), pid=os.getpid())
        conn.commit()
    resume_discover = job_row(conn)["state"] == "discovering" and bool(job_row(conn)["discover_cursor"])
    processed = 0
    remaining = limit if limit is not None else 10**12

    def drain_some() -> None:
        nonlocal processed, remaining
        if remaining <= 0:
            return
        size = min(batch_size, remaining)
        n = process_batch(conn, xml_root, batch_size=size)
        processed += n
        remaining -= n

    discover(conn, xml_root, resume=resume_discover, after_month=drain_some)
    while remaining > 0:
        size = min(batch_size, remaining)
        n = process_batch(conn, xml_root, batch_size=size)
        processed += n
        remaining -= n
        if n == 0:
            break
    if pending_count(conn) == 0:
        _set_state(conn, "complete", pid=os.getpid())
        conn.commit()
    return processed


def run_walk(
    conn,
    xml_root: Path,
    *,
    once: bool = True,
    batch_size: int = BATCH_SIZE,
    limit: int | None = None,
    poll_seconds: int = 300,
    lock_path: Path | None = None,
) -> dict:
    handle = None
    if lock_path is not None:
        handle = acquire_lock(lock_path)
        if handle is None:
            return {"state": "locked", "coverage": coverage(conn)}
    try:
        total = 0
        while True:
            n = tick(conn, xml_root, batch_size=batch_size, limit=limit)
            total += n
            if once:
                break
            if n == 0:
                time.sleep(poll_seconds)
            if limit is not None and total >= limit:
                break
        return {"state": job_row(conn)["state"], "processed": total, "coverage": coverage(conn)}
    except Exception as exc:
        _set_state(conn, "failed", last_error=repr(exc), pid=os.getpid())
        conn.commit()
        raise
    finally:
        if handle is not None:
            handle.close()
