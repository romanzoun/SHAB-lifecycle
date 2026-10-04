from shab_harvester import db


def test_init_db_creates_tables(conn):
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"import_day", "publication_queue", "shab_publication_raw"} <= tables


def test_get_connection_enables_wal_mode(tmp_path):
    """WAL lets a reader (status.sh etc.) run while the scraper holds a
    write transaction open, instead of raising 'database is locked' —
    this happened for real on the production run."""
    db_path = tmp_path / "wal_test.sqlite"
    db.init_db(db_path)
    conn = db.get_connection(db_path)
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode == "wal"
    finally:
        conn.close()


def test_reader_does_not_get_locked_out_during_writer_transaction(tmp_path):
    db_path = tmp_path / "wal_concurrency_test.sqlite"
    db.init_db(db_path)

    writer = db.get_connection(db_path)
    writer.execute("BEGIN")
    writer.execute("INSERT INTO import_day (publication_date, status) VALUES ('2018-09-03', 'pending')")
    # Writer transaction left open (not yet committed) while a reader connects.

    reader = db.get_connection(db_path)
    try:
        # Must not raise "database is locked" thanks to WAL.
        count = db.scalar(reader, "SELECT COUNT(*) FROM import_day")
        assert count == 0  # writer hasn't committed yet, reader sees the old snapshot
    finally:
        reader.close()
        writer.commit()
        writer.close()


def test_seed_day_is_idempotent(conn):
    db.seed_day(conn, "2018-09-03")
    db.seed_day(conn, "2018-09-03")
    rows = conn.execute("SELECT * FROM import_day WHERE publication_date = '2018-09-03'").fetchall()
    assert len(rows) == 1
    assert rows[0]["status"] == "pending"


def test_import_day_state_machine_empty(conn):
    db.seed_day(conn, "2018-09-03")
    db.mark_day_running(conn, "2018-09-03")
    day = db.get_import_day(conn, "2018-09-03")
    assert day["status"] == "running"
    assert day["attempt_count"] == 1

    db.mark_day_empty(conn, "2018-09-03")
    day = db.get_import_day(conn, "2018-09-03")
    assert day["status"] == "empty"
    assert day["result_count"] == 0


def test_import_day_state_machine_discovered_then_completed(conn):
    db.seed_day(conn, "2018-09-03")
    db.mark_day_running(conn, "2018-09-03")
    db.mark_day_discovered(conn, "2018-09-03", result_count=2, discovered_count=2)

    day = db.get_import_day(conn, "2018-09-03")
    assert day["status"] == "discovered"
    assert day["result_count"] == 2

    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", "info", "url-1")
    db.upsert_queue_item(conn, "pub-2", "2018-09-03", "HR01-2", "Title 2", "info", "url-2")
    db.mark_queue_item_scraped(conn, "pub-1")
    db.mark_queue_item_scraped(conn, "pub-2")

    db.update_day_scraped_count(conn, "2018-09-03")
    day = db.get_import_day(conn, "2018-09-03")
    assert day["scraped_count"] == 2
    assert day["status"] == "completed"


def test_import_day_failed_and_reset(conn):
    db.seed_day(conn, "2018-09-03")
    db.mark_day_failed(conn, "2018-09-03", "boom")
    day = db.get_import_day(conn, "2018-09-03")
    assert day["status"] == "failed"
    assert day["last_error"] == "boom"

    reset_count = db.reset_failed_days(conn)
    assert reset_count == 1
    day = db.get_import_day(conn, "2018-09-03")
    assert day["status"] == "pending"


def test_exhausted_failure_archived_as_non_public(conn):
    db.upsert_queue_item(
        conn,
        "pub-np",
        "2021-07-02",
        None,
        "Bankruptcy Markus Brenner",
        "02.07.2021 - KK02-0000019796 - SOGC - Bankruptcies",
        "https://www.shab.ch/#!/search/publications/detail/pub-np",
    )
    # Simulate 3 scrape attempts that fail
    for _ in range(3):
        db.mark_queue_item_running(conn, "pub-np")
        db.mark_queue_item_failed(conn, "pub-np", "timeout")
    assert db.maybe_archive_exhausted_failure(conn, "pub-np") is True

    q = conn.execute("SELECT status FROM publication_queue WHERE publication_id='pub-np'").fetchone()
    assert q["status"] == "non_public"
    np = conn.execute(
        "SELECT * FROM shab_publication_non_public WHERE publication_id='pub-np'"
    ).fetchone()
    assert np is not None
    assert np["availability"] == "non_public"
    assert np["title"] == "Bankruptcy Markus Brenner"
    assert np["source_ref"] == "KK02-0000019796"
    assert np["rubric"] == "Bankruptcies"
    assert "shab.ch" in np["detail_url"]


def test_archive_exhausted_failures_batch(conn):
    db.upsert_queue_item(conn, "a", "2020-01-01", None, "T", "01.01.2020 - X - Rubrik", "url-a")
    db.upsert_queue_item(conn, "b", "2020-01-02", None, "T2", "info", "url-b")
    for pid in ("a", "b"):
        for _ in range(3):
            db.mark_queue_item_running(conn, pid)
            db.mark_queue_item_failed(conn, pid, "gone")
    assert db.archive_exhausted_failures(conn) == 2
    assert db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_non_public") == 2


def test_reset_failed_also_recovers_stuck_running_rows(conn):
    """A process crash can leave a day/queue-item stuck in 'running' forever
    (never marked failed) — pending_queue_items()/pending_or_failed_days()
    don't select 'running', so it would otherwise never be retried."""
    db.seed_day(conn, "2018-09-03")
    db.mark_day_running(conn, "2018-09-03")
    assert db.get_import_day(conn, "2018-09-03")["status"] == "running"

    db.upsert_queue_item(conn, "pub-1", "2018-09-03", None, None, None, None)
    db.mark_queue_item_running(conn, "pub-1")
    assert db.get_queue_item(conn, "pub-1")["status"] == "running"

    days_reset = db.reset_failed_days(conn)
    queue_reset = db.reset_failed_queue_items(conn)

    assert days_reset == 1
    assert queue_reset == 1
    assert db.get_import_day(conn, "2018-09-03")["status"] == "pending"
    assert db.get_queue_item(conn, "pub-1")["status"] == "pending"


def test_reclaim_stale_running_queue_items(conn):
    """In the single-worker model, a 'running' row at the start of a new
    scrape run can only be a crash leftover (no sibling worker holds it)."""
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", None, None, None, None)
    db.upsert_queue_item(conn, "pub-2", "2018-09-03", None, None, None, None)
    db.mark_queue_item_running(conn, "pub-1")
    db.mark_queue_item_scraped(conn, "pub-2")

    reclaimed = db.reclaim_stale_running_queue_items(conn)

    assert reclaimed == 1
    assert db.get_queue_item(conn, "pub-1")["status"] == "pending"
    assert db.get_queue_item(conn, "pub-2")["status"] == "scraped"  # untouched


def test_upsert_queue_item_does_not_overwrite_existing_fields(conn):
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Original Title", "info", "url-1")
    # Re-discovery with different/missing data must not clobber existing values.
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", None, None, "info", "url-1")

    row = conn.execute(
        "SELECT * FROM publication_queue WHERE publication_id = 'pub-1'"
    ).fetchone()
    assert row["title"] == "Original Title"
    assert row["publication_number"] == "HR01-1"
    assert row["status"] == "pending"


def test_pending_queue_items_respects_attempt_limit(conn):
    db.upsert_queue_item(conn, "pub-pending", "2018-09-03", None, None, None, None)
    db.upsert_queue_item(conn, "pub-failed-ok", "2018-09-03", None, None, None, None)
    db.upsert_queue_item(conn, "pub-failed-exhausted", "2018-09-03", None, None, None, None)
    db.upsert_queue_item(conn, "pub-scraped", "2018-09-03", None, None, None, None)

    db.mark_queue_item_failed(conn, "pub-failed-ok", "transient error")
    db.mark_queue_item_scraped(conn, "pub-scraped")

    # Push pub-failed-exhausted to attempt_count = 3 (its limit).
    for _ in range(3):
        db.mark_queue_item_running(conn, "pub-failed-exhausted")
    db.mark_queue_item_failed(conn, "pub-failed-exhausted", "still failing")

    pending = {row["publication_id"] for row in db.pending_queue_items(conn, limit=100)}
    assert "pub-pending" in pending
    assert "pub-failed-ok" in pending
    assert "pub-scraped" not in pending
    assert "pub-failed-exhausted" not in pending


def test_repair_queue_status_fixes_orphaned_raw_rows(conn):
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", None, None, None, None)
    db.upsert_publication_raw(conn, {"publication_id": "pub-1", "publication_date": "2018-09-03"})

    row = conn.execute("SELECT status FROM publication_queue WHERE publication_id = 'pub-1'").fetchone()
    assert row["status"] == "pending"

    repaired = db.repair_queue_status(conn)
    assert repaired == 1

    row = conn.execute("SELECT status FROM publication_queue WHERE publication_id = 'pub-1'").fetchone()
    assert row["status"] == "scraped"


def test_day_overview_reports_state_machine_per_publication(conn):
    db.seed_day(conn, "2018-09-03")
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", None, None)
    db.upsert_queue_item(conn, "pub-2", "2018-09-03", "HR01-2", "Title 2", None, None)
    db.upsert_queue_item(conn, "pub-3", "2018-09-03", "HR01-3", "Title 3", None, None)

    db.mark_queue_item_scraped(conn, "pub-1")
    db.upsert_publication_raw(conn, {"publication_id": "pub-1", "publication_date": "2018-09-03"})
    db.mark_queue_item_failed(conn, "pub-2", "boom")
    # pub-3 stays pending.

    rows = db.day_overview(conn, "2018-09-03")
    by_id = {row["publication_id"]: row for row in rows}

    assert by_id["pub-1"]["status"] == "scraped"
    assert by_id["pub-1"]["has_raw"] == 1
    assert by_id["pub-2"]["status"] == "failed"
    assert by_id["pub-2"]["last_error"] == "boom"
    assert by_id["pub-3"]["status"] == "pending"
    assert by_id["pub-3"]["has_raw"] == 0

    failed_only = db.day_overview(conn, "2018-09-03", status="failed")
    assert {row["publication_id"] for row in failed_only} == {"pub-2"}
