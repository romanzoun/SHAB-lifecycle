from pathlib import Path

import pytest
from shab_analyzer import store, warehouse
from shab_analyzer.parse import parse_publication_xml

FIXTURES = Path(__file__).parent / "fixtures"


def _load(tmp_path: Path):
    analyzer = store.connect(tmp_path / "a.sqlite")
    for xml in FIXTURES.glob("*.xml"):
        result = parse_publication_xml(xml, publication_id=xml.stem)
        store.replace_parse(analyzer, result)
    wh = warehouse.connect(tmp_path / "w.sqlite")
    warehouse.replay_from_analyzer(analyzer, wh)
    return analyzer, wh


@pytest.fixture(scope="module")
def warehouse_seed(tmp_path_factory):
    analyzer, wh = _load(tmp_path_factory.mktemp("warehouse-lenses"))
    try:
        yield analyzer, wh
    finally:
        analyzer.close()
        wh.close()


@pytest.fixture
def loaded_warehouse(warehouse_seed, tmp_path):
    analyzer = store.connect(tmp_path / "a.sqlite")
    wh = warehouse.connect(tmp_path / "w.sqlite")
    try:
        warehouse_seed[0].backup(analyzer)
        warehouse_seed[1].backup(wh)
        yield analyzer, wh
    finally:
        analyzer.close()
        wh.close()


def test_person_lens_includes_signing_and_related_org(loaded_warehouse):
    _, wh = loaded_warehouse
    people = wh.execute(
        "SELECT DISTINCT person_key FROM fact_event WHERE person_key LIKE '%heck%'"
    ).fetchall()
    assert people
    key = people[0]["person_key"]
    timeline = warehouse.lens_timeline(wh, "person", key)
    assert timeline
    assert any(row["signing"] for row in timeline)
    related = warehouse.related_org_events(wh, key)
    assert any(row["org_uid"] == "CHE-110.028.408" for row in related)
    assert any(
        row["event_type"] in ("seat_changed", "address_changed") for row in related
    )


def test_plz_pulse_and_people(loaded_warehouse):
    _, wh = loaded_warehouse
    pulse = warehouse.lens_pulse(wh, "plz", "6340")
    assert pulse
    assert all(row["month"] for row in pulse)
    people = warehouse.plz_people(wh, "6340")
    assert people
    canton = warehouse.lens_timeline(wh, "canton", "ZG")
    assert canton
    org = warehouse.lens_timeline(wh, "org", "CHE-110.028.408")
    assert org
