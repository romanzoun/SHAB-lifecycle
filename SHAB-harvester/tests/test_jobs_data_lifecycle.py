from shab_harvester import db, jobs


def _make_sample_data(db_path, raw_html_dir, raw_xml_dir):
    db.init_db(db_path)
    with db.connect(db_path) as conn:
        db.seed_day(conn, "2018-09-03")
        db.upsert_publication_raw(conn, {"publication_id": "pub-1", "publication_date": "2018-09-03"})

    (raw_html_dir / "2018" / "09").mkdir(parents=True)
    (raw_html_dir / "2018" / "09" / "pub-1.html").write_text("<html>hello</html>")
    (raw_xml_dir / "2018" / "09").mkdir(parents=True)
    (raw_xml_dir / "2018" / "09" / "pub-1.xml").write_text("<xml>hello</xml>")


def test_reset_all_refuses_without_confirmation(tmp_path):
    db_path = tmp_path / "test.sqlite"
    raw_html_dir = tmp_path / "raw_html"
    raw_xml_dir = tmp_path / "raw_xml"
    db.init_db(db_path)
    db_path_mtime_before = db_path.stat().st_mtime

    logs = []
    jobs.reset_all(confirm=False, log=logs.append, db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir)

    assert db_path.exists()
    assert db_path.stat().st_mtime == db_path_mtime_before
    assert any("Refusing" in line for line in logs)


def test_reset_all_wipes_db_and_raw_dirs_when_confirmed(tmp_path):
    db_path = tmp_path / "test.sqlite"
    raw_html_dir = tmp_path / "raw_html"
    raw_xml_dir = tmp_path / "raw_xml"
    _make_sample_data(db_path, raw_html_dir, raw_xml_dir)

    logs = []
    jobs.reset_all(confirm=True, log=logs.append, db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir)

    assert not list(raw_html_dir.glob("**/*.html"))
    assert raw_html_dir.exists()  # recreated empty
    assert raw_xml_dir.exists()

    with db.connect(db_path) as conn:
        assert db.scalar(conn, "SELECT COUNT(*) FROM import_day") == 0
        assert db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw") == 0
        tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        assert "import_day" in tables
        assert "organizations" in tables


def test_export_data_creates_timestamped_zip_with_db_and_raw_files(tmp_path):
    db_path = tmp_path / "test.sqlite"
    raw_html_dir = tmp_path / "raw_html"
    raw_xml_dir = tmp_path / "raw_xml"
    export_dir = tmp_path / "exports"
    _make_sample_data(db_path, raw_html_dir, raw_xml_dir)

    logs = []
    zip_path = jobs.export_data(
        log=logs.append, db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir, export_dir=export_dir
    )

    assert zip_path.exists()
    assert zip_path.name.startswith("shab_export_")
    assert zip_path.suffix == ".zip"

    import zipfile
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert "shab_harvester.sqlite" in names
    assert "raw_html/2018/09/pub-1.html" in names
    assert "raw_xml/2018/09/pub-1.xml" in names


def test_list_exports_sorted_newest_first(tmp_path):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    (export_dir / "shab_export_20180101-000000.zip").write_bytes(b"")
    (export_dir / "shab_export_20990101-000000.zip").write_bytes(b"")

    exports = jobs.list_exports(export_dir)
    assert exports[0].name == "shab_export_20990101-000000.zip"
    assert exports[1].name == "shab_export_20180101-000000.zip"


def test_list_exports_empty_dir_returns_empty_list(tmp_path):
    assert jobs.list_exports(tmp_path / "does-not-exist") == []


def test_import_data_refuses_without_confirmation(tmp_path):
    zip_path = tmp_path / "fake.zip"
    zip_path.write_bytes(b"")
    db_path = tmp_path / "restored" / "test.sqlite"

    logs = []
    jobs.import_data(zip_path, confirm=False, log=logs.append, db_path=db_path,
                      raw_html_dir=tmp_path / "restored" / "raw_html", raw_xml_dir=tmp_path / "restored" / "raw_xml")

    assert any("Refusing" in line for line in logs)
    assert not db_path.exists()


def test_import_data_missing_zip_logs_error_not_exception(tmp_path):
    logs = []
    jobs.import_data(
        tmp_path / "does-not-exist.zip", confirm=True, log=logs.append,
        db_path=tmp_path / "test.sqlite", raw_html_dir=tmp_path / "raw_html", raw_xml_dir=tmp_path / "raw_xml",
    )
    assert any("not found" in line for line in logs)


def test_export_then_delete_then_import_round_trip(tmp_path):
    db_path = tmp_path / "test.sqlite"
    raw_html_dir = tmp_path / "raw_html"
    raw_xml_dir = tmp_path / "raw_xml"
    export_dir = tmp_path / "exports"
    _make_sample_data(db_path, raw_html_dir, raw_xml_dir)

    zip_path = jobs.export_data(
        db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir, export_dir=export_dir
    )

    jobs.reset_all(confirm=True, db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir)
    with db.connect(db_path) as conn:
        assert db.scalar(conn, "SELECT COUNT(*) FROM shab_publication_raw") == 0
    assert not (raw_html_dir / "2018" / "09" / "pub-1.html").exists()

    logs = []
    jobs.import_data(
        zip_path, confirm=True, log=logs.append,
        db_path=db_path, raw_html_dir=raw_html_dir, raw_xml_dir=raw_xml_dir,
    )

    with db.connect(db_path) as conn:
        row = conn.execute("SELECT * FROM shab_publication_raw WHERE publication_id = 'pub-1'").fetchone()
        assert row is not None
        assert row["publication_date"] == "2018-09-03"

    assert (raw_html_dir / "2018" / "09" / "pub-1.html").read_text() == "<html>hello</html>"
    assert (raw_xml_dir / "2018" / "09" / "pub-1.xml").read_text() == "<xml>hello</xml>"

    # The export zip itself must survive the delete step (it lives outside raw_html/raw_xml/db_path).
    assert zip_path.exists()
