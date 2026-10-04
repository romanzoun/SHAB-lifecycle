import time

from shab_harvester import analysis, db, webui


def test_render_harvest_lists_forms_and_no_jobs_initially():
    body = webui.render_harvest().decode("utf-8")
    for cmd in webui.JOB_COMMANDS:
        assert cmd in body
    assert "No jobs started yet" in body


def test_render_harvest_groups_commands_into_segments_with_explanations():
    body = webui.render_harvest().decode("utf-8")
    for segment in webui.SEGMENTS:
        assert segment["title"] in body
        assert "Danach hast du" in body
    # Data segment commands should appear before Discover segment commands.
    assert body.index("Data Segment") < body.index("Discover Segment") < body.index("Scrape Segment")


def test_render_harvest_import_form_shows_hint_when_no_exports_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(webui.jobs, "EXPORT_DIR", tmp_path / "no-exports-here")
    body = webui.render_harvest().decode("utf-8")
    assert "Noch kein Export vorhanden" in body


def test_render_harvest_import_form_lists_available_exports(tmp_path, monkeypatch):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    (export_dir / "shab_export_20260101-000000.zip").write_bytes(b"")
    monkeypatch.setattr(webui.jobs, "EXPORT_DIR", export_dir)

    body = webui.render_harvest().decode("utf-8")
    assert "shab_export_20260101-000000.zip" in body


def test_build_job_target_import_data_rejects_path_traversal(tmp_path, monkeypatch):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    monkeypatch.setattr(webui.jobs, "EXPORT_DIR", export_dir)

    target = webui._build_job_target("import-data", {"zip": ["../../etc/passwd"], "confirm": ["IMPORT"]})
    logs = []
    target(logs.append)
    assert any("Invalid export file" in line for line in logs)


def test_build_job_target_import_data_requires_exact_confirm_text(tmp_path, monkeypatch):
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    zip_path = export_dir / "shab_export_20260101-000000.zip"
    zip_path.write_bytes(b"")
    monkeypatch.setattr(webui.jobs, "EXPORT_DIR", export_dir)

    target = webui._build_job_target("import-data", {"zip": [zip_path.name], "confirm": ["nope"]})
    logs = []
    target(logs.append)
    assert any("Refusing" in line for line in logs)


def test_job_manager_runs_target_and_records_log():
    manager = webui.JobManager()

    def target(log):
        log("step 1")
        log("step 2")

    job_id = manager.start("unit-test", {}, target)
    for _ in range(50):
        job = manager.get(job_id)
        if job["status"] != "running":
            break
        time.sleep(0.02)

    assert job["status"] == "success"
    assert job["log"] == ["step 1", "step 2"]
    assert job["finished_at"] is not None


def test_job_manager_records_failure():
    manager = webui.JobManager()

    def target(log):
        raise ValueError("boom")

    job_id = manager.start("unit-test-fail", {}, target)
    for _ in range(50):
        job = manager.get(job_id)
        if job["status"] != "running":
            break
        time.sleep(0.02)

    assert job["status"] == "failed"
    assert any("boom" in line for line in job["log"])


def test_render_job_unknown_id():
    body = webui.render_job(None, "missing").decode("utf-8")
    assert "Unknown job" in body


def test_build_job_target_dispatches_known_commands():
    for cmd in webui.JOB_COMMANDS:
        target = webui._build_job_target(cmd, {})
        assert target is not None, cmd


def test_build_job_target_rejects_unknown_command():
    assert webui._build_job_target("not-a-real-command", {}) is None


def test_reset_all_target_refuses_without_exact_confirm_text():
    # Safe to actually run: confirm=False short-circuits before touching any files.
    target = webui._build_job_target("reset-all", {"confirm": ["not quite"]})
    logs = []
    target(logs.append)
    assert any("Refusing" in line for line in logs)


def test_reset_all_target_requires_uppercase_reset_literal():
    target = webui._build_job_target("reset-all", {"confirm": ["reset"]})  # lowercase must not count
    logs = []
    target(logs.append)
    assert any("Refusing" in line for line in logs)


def test_render_organizations_empty_state(conn):
    body = webui.render_organizations(conn, None).decode("utf-8")
    assert "run `analyze`" in body or "analyze" in body


def test_render_organizations_and_detail_after_analyze(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-09-03",
            "uid": "CHE-108.472.828",
            "company_block_text": "Richard Fitzi AG",
            "canton": "SG",
            "category": "Commercial Registry entries",
            "subcategory": "Change",
            "title": "Change Richard Fitzi AG",
            "body_text": "Eingetragene Personen neu oder mutierend: Fitzi, Richard, von Gais, in Altstätten, "
                         "Mitglied des Verwaltungsrates und Liquidator, mit Einzelunterschrift.",
        },
    )
    analysis.run_aggregate(conn)

    listing = webui.render_organizations(conn, None).decode("utf-8")
    assert "Richard Fitzi AG" in listing
    assert "CHE-108.472.828" in listing

    detail = webui.render_organization(conn, "uid:CHE-108.472.828").decode("utf-8")
    assert "Fitzi, Richard" in detail
    assert "Mitglied des Verwaltungsrates und Liquidator" in detail


def test_render_organization_unknown_key(conn):
    body = webui.render_organization(conn, "uid:does-not-exist").decode("utf-8")
    assert "Unknown organization" in body


def test_render_cases_and_detail_after_analyze(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-09-03",
            "uid": "CHE-108.472.828",
            "company_block_text": "Richard Fitzi AG",
            "canton": "SG",
            "category": "Commercial Registry entries",
            "subcategory": "Change",
            "title": "title",
            "body_text": "Mit Urteil vom 28.08.2018 hat der Konkursrichter des Bezirksgerichts Uster "
                         "über die Gesellschaft den Konkurs eröffnet.",
        },
    )
    analysis.run_aggregate(conn)

    listing = webui.render_cases(conn).decode("utf-8")
    assert "BANKRUPTCY" in listing
    assert "uid:CHE-108.472.828:BANKRUPTCY" in listing

    detail = webui.render_case(conn, "uid:CHE-108.472.828:BANKRUPTCY").decode("utf-8")
    assert "Konkursrichter" in detail
    assert "BANKRUPTCY_OPENED" in detail


def test_render_case_unknown_id(conn):
    body = webui.render_case(conn, "does-not-exist").decode("utf-8")
    assert "Unknown case" in body
