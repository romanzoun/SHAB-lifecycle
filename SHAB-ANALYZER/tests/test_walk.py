from pathlib import Path
from shutil import copyfile

from shab_analyzer import store
from shab_analyzer.walk import coverage, run_walk, tick

FIXTURES = Path(__file__).parent / "fixtures"


def _copy_named(tmp: Path, stem: str) -> None:
    src = FIXTURES / f"{stem}.xml"
    dest_dir = tmp / "2026" / "09"
    dest_dir.mkdir(parents=True, exist_ok=True)
    copyfile(src, dest_dir / f"{stem}.xml")


def test_walk_resumes_after_limit_and_stale_pid(tmp_path):
    xml_root = tmp_path / "xml"
    _copy_named(xml_root, "a3d86d90-4b95-4f57-8a98-d70ad9dbdf05")
    _copy_named(xml_root, "085a33cb-1839-4246-8050-97466a7f9a39")
    db = tmp_path / "a.sqlite"
    lock = tmp_path / "walk.lock"
    conn = store.connect(db)
    first = run_walk(conn, xml_root, once=True, limit=1, batch_size=1, lock_path=lock)
    assert first["processed"] == 1
    assert coverage(conn)["pending"] == 1

    conn.execute(
        "UPDATE walk_job SET state='walking', pid=999999999, heartbeat_at='2000-01-01T00:00:00Z' WHERE id=1"
    )
    conn.commit()
    second = run_walk(conn, xml_root, once=True, lock_path=lock)
    assert second["processed"] == 1
    cov = coverage(conn)
    assert cov["pending"] == 0
    assert cov["job_state"] == "complete"
    assert cov["items"].get("ok", 0) == 2
    conn.close()


def test_walk_error_continues(tmp_path):
    xml_root = tmp_path / "xml"
    dest = xml_root / "2026" / "09"
    dest.mkdir(parents=True)
    (dest / "broken.xml").write_text("not xml", encoding="utf-8")
    copyfile(FIXTURES / "feddc02f-6eb7-44bb-bf61-ecd5801e1f06.xml", dest / "feddc02f-6eb7-44bb-bf61-ecd5801e1f06.xml")
    conn = store.connect(tmp_path / "a.sqlite")
    result = run_walk(conn, xml_root, once=True, lock_path=tmp_path / "walk.lock")
    cov = coverage(conn)
    assert result["state"] == "complete"
    assert cov["items"].get("error") == 1
    assert cov["items"].get("ok") == 1
    conn.close()


def test_non_hr_deferred_until_family_unlocked():
    from shab_analyzer.models import ParseResult
    from shab_analyzer.walk import _item_status

    result = ParseResult(
        publication_id="x",
        published_at="2026-01-01",
        language="de",
        sub_rubric="KK01",
        org_uid=None,
        canton=None,
        plz=None,
        events=[],
        leftover_text="konkurs",
        status="PARTIALLY_PARSED",
    )
    assert _item_status(result, ("HR",)) == "deferred"
    assert _item_status(result, ("HR", "KK")) == "partial"
    hr = ParseResult(
        publication_id="y",
        published_at="2026-01-01",
        language="de",
        sub_rubric="HR02",
        org_uid=None,
        canton=None,
        plz=None,
        events=[],
        leftover_text="",
        status="FULLY_PARSED",
    )
    assert _item_status(hr, ("HR", "KK")) == "ok"


def test_tick_skips_already_parsed(tmp_path):
    xml_root = tmp_path / "xml"
    _copy_named(xml_root, "e51ee4b5-9bde-4b25-82e3-79e5c5a5be24")
    conn = store.connect(tmp_path / "a.sqlite")
    assert tick(conn, xml_root) == 1
    assert tick(conn, xml_root) == 0
    conn.close()
