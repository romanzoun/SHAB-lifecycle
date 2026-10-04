from shab_harvester import db, webui


def test_render_overview_lists_days(conn):
    db.seed_day(conn, "2018-09-03")
    db.mark_day_discovered(conn, "2018-09-03", result_count=2, discovered_count=2)
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", None, None)
    db.mark_queue_item_scraped(conn, "pub-1")

    body = webui.render_overview(conn).decode("utf-8")
    assert "2018-09-03" in body
    assert "discovered" in body
    assert "1/1" in body  # only pub-1 is in publication_queue


def test_render_day_lists_publications_and_respects_filter(conn):
    db.seed_day(conn, "2018-09-03")
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", None, None)
    db.upsert_queue_item(conn, "pub-2", "2018-09-03", "HR01-2", "Title 2", None, None)
    db.mark_queue_item_failed(conn, "pub-2", "boom")

    body = webui.render_day(conn, "2018-09-03", None).decode("utf-8")
    assert "pub-1" in body
    assert "pub-2" in body
    assert "boom" in body

    filtered = webui.render_day(conn, "2018-09-03", "failed").decode("utf-8")
    assert "pub-2" in filtered
    assert "pub-1" not in filtered


def test_render_day_handles_unknown_date(conn):
    body = webui.render_day(conn, "2099-01-01", None).decode("utf-8")
    assert "No import_day" in body


def test_render_overview_escapes_html_in_titles(conn):
    db.seed_day(conn, "2018-09-03")
    db.upsert_queue_item(
        conn, "pub-1", "2018-09-03", "HR01-1", "<script>alert(1)</script>", None, None
    )
    body = webui.render_day(conn, "2018-09-03", None).decode("utf-8")
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def test_render_publication_not_scraped_yet(conn):
    db.seed_day(conn, "2018-09-03")
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", None, None)

    body = webui.render_publication(conn, "pub-1").decode("utf-8")
    assert "Not scraped yet" in body
    assert "pub-1" in body


def test_render_publication_unknown_id(conn):
    body = webui.render_publication(conn, "does-not-exist").decode("utf-8")
    assert "Unknown publication_id" in body


def test_render_publication_shows_raw_fields_and_links(conn):
    db.seed_day(conn, "2018-09-03")
    db.upsert_queue_item(conn, "pub-1", "2018-09-03", "HR01-1", "Title 1", None, None)
    db.mark_queue_item_scraped(conn, "pub-1")
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-09-03",
            "uid": "CHE-108.472.828",
            "zefix_url": "http://www.zefix.admin.ch/de/search/entity/list?name=CHE-108.472.828",
            "body_text": "<b>raw text</b>",
            "raw_metadata_json": '{"Status": ["PUBLISHED"]}',
        },
    )

    body = webui.render_publication(conn, "pub-1").decode("utf-8")
    assert "CHE-108.472.828" in body
    assert "zefix.admin.ch" in body
    assert "<b>raw text</b>" not in body  # body_text must be escaped
    assert "&lt;b&gt;raw text&lt;/b&gt;" in body
    assert "Status" in body  # raw_metadata_json dumped as <pre>


def test_resolve_raw_file_rejects_path_traversal():
    assert webui._resolve_raw_file("../../../etc/passwd") is None
    assert webui._resolve_raw_file("data/raw_html/2099/01/does-not-exist.html") is None
