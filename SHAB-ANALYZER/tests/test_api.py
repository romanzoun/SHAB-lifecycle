from pathlib import Path

from fastapi.testclient import TestClient

from shab_analyzer import store, warehouse
from shab_analyzer.api import app, set_warehouse_path
from shab_analyzer.parse import parse_publication_xml

FIXTURES = Path(__file__).parent / "fixtures"


def test_lens_api_person_and_plz(tmp_path):
    analyzer = store.connect(tmp_path / "a.sqlite")
    for xml in FIXTURES.glob("*.xml"):
        store.replace_parse(analyzer, parse_publication_xml(xml, publication_id=xml.stem))
    wh_path = tmp_path / "w.sqlite"
    wh = warehouse.connect(wh_path)
    warehouse.replay_from_analyzer(analyzer, wh)
    set_warehouse_path(wh_path)
    client = TestClient(app)
    key = wh.execute(
        "SELECT person_key FROM fact_event WHERE person_key LIKE '%heck%' LIMIT 1"
    ).fetchone()["person_key"]
    person = client.get(f"/lens/person/{key}").json()
    assert person["series"]
    assert person["related_org_events"]
    plz = client.get("/lens/plz/6340", params={"mode": "pulse"}).json()
    assert plz["series"]
    assert "people" in plz
    bad = client.get("/lens/unknown/x")
    assert bad.status_code == 400
