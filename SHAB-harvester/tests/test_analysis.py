from shab_harvester import analysis, db


def test_classify_event_keyword_bankruptcy_opened():
    result = analysis.classify_event(
        "Commercial Registry entries", "Change", "title",
        "Mit Urteil vom 28.08.2018 hat der Konkursrichter des Bezirksgerichts Uster "
        "über die Gesellschaft den Konkurs eröffnet.",
    )
    assert result["event_type"] == "BANKRUPTCY_OPENED"
    assert result["case_type"] == "BANKRUPTCY"


def test_classify_event_keyword_no_assets():
    result = analysis.classify_event(
        "Commercial Registry entries", "Change", "title",
        "Das Konkursverfahren ist mit Urteil des Konkursrichters mangels Aktiven eingestellt worden.",
    )
    assert result["event_type"] == "BANKRUPTCY_CLOSED_NO_ASSETS"
    assert result["case_type"] == "BANKRUPTCY"


def test_classify_event_falls_back_to_subcategory():
    result = analysis.classify_event("Commercial Registry entries", "New entry", "title", "some neutral body text")
    assert result["event_type"] == "ORG_NEW"
    assert result["confidence"] == "metadata"


def test_classify_event_unknown_falls_back_to_other():
    result = analysis.classify_event(None, None, "title", "nothing relevant here")
    assert result["event_type"] == "OTHER"
    assert result["confidence"] == "fallback"


def test_extract_persons_added_mutation():
    text = (
        "Richard Fitzi AG Uhren und Schmuck, in Altstätten, CHE-108.472.828. "
        "Eingetragene Personen neu oder mutierend: Fitzi, Richard, von Gais, in Altstätten, "
        "Mitglied des Verwaltungsrates und Liquidator, mit Einzelunterschrift."
    )
    persons = analysis.extract_persons(text)
    assert len(persons) == 1
    assert persons[0]["full_name"] == "Fitzi, Richard"
    assert persons[0]["place"] == "Altstätten"
    assert persons[0]["role"] == "Mitglied des Verwaltungsrates und Liquidator"
    assert persons[0]["mutation_action"] == "added"


def test_extract_persons_removed_mutation():
    text = (
        "Wohngenossenschaft im Grienboden, in Riehen, CHE-102.340.602. "
        "Ausgeschiedene Personen und erloschene Unterschriften: Jurisic, Ivan, von Basel, in Riehen, "
        "Mitglied der Verwaltung, Kassier, mit Kollektivunterschrift zu zweien."
    )
    persons = analysis.extract_persons(text)
    assert len(persons) == 1
    assert persons[0]["full_name"] == "Jurisic, Ivan"
    assert persons[0]["mutation_action"] == "removed"
    assert "Kollektivunterschrift" in persons[0]["signing_authority"]


def test_extract_persons_returns_empty_for_unstructured_text():
    assert analysis.extract_persons("Just some random publication text with no mutation list.") == []
    assert analysis.extract_persons(None) == []


def test_build_org_key_prefers_uid(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-09-03",
            "uid": "CHE-108.472.828",
            "company_block_text": "Richard Fitzi AG",
            "canton": "SG",
        },
    )
    row = db.get_publication_raw(conn, "pub-1")
    org_key, uid, confidence = analysis.build_org_key(row)
    assert org_key == "uid:CHE-108.472.828"
    assert uid == "CHE-108.472.828"
    assert confidence == "HIGH"


def test_build_org_key_falls_back_to_name_and_canton(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-2",
            "publication_date": "2018-09-03",
            "uid": None,
            "company_block_text": "Muster AG",
            "canton": "ZH",
        },
    )
    row = db.get_publication_raw(conn, "pub-2")
    org_key, uid, confidence = analysis.build_org_key(row)
    assert org_key == "cand:muster ag|ZH"
    assert uid is None
    assert confidence == "LOW"


def test_run_aggregate_builds_organization_and_case(conn):
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
            "body_text": (
                "Mit Urteil vom 28.08.2018 hat der Konkursrichter des Bezirksgerichts Uster "
                "über die Gesellschaft den Konkurs eröffnet."
            ),
        },
    )

    processed = analysis.run_aggregate(conn)
    assert processed == 1

    org = db.get_organization(conn, "uid:CHE-108.472.828")
    assert org is not None
    assert org["publication_count"] == 1
    assert org["match_confidence"] == "HIGH"

    cases = db.organization_cases(conn, "uid:CHE-108.472.828")
    assert len(cases) == 1
    assert cases[0]["case_type"] == "BANKRUPTCY"
    assert cases[0]["status"] == "open"

    # Re-running without --force must be a no-op (content_hash unchanged).
    processed_again = analysis.run_aggregate(conn)
    assert processed_again == 0


def test_run_aggregate_force_reprocesses(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-09-03",
            "uid": "CHE-108.472.828",
            "company_block_text": "Richard Fitzi AG",
            "canton": "SG",
            "category": "Commercial Registry entries",
            "subcategory": "New entry",
            "title": "title",
            "body_text": "neutral body",
        },
    )
    analysis.run_aggregate(conn)
    assert analysis.run_aggregate(conn) == 0
    assert analysis.run_aggregate(conn, force=True) == 1


def test_run_aggregate_picks_date_nearest_keyword_not_first_date_in_text(conn):
    db.upsert_publication_raw(
        conn,
        {
            "publication_id": "pub-1",
            "publication_date": "2018-08-28",
            "uid": "CHE-342.219.250",
            "company_block_text": "Seli Bau GmbH",
            "canton": "ZH",
            "category": "Commercial Registry entries",
            "subcategory": "Change",
            "title": "title",
            "body_text": (
                "Seli Bau GmbH, in Wangen-Brüttisellen, CHE-342.219.250 "
                "(SHAB Nr. 98 vom 22.05.2014, Publ. 1515751). Firma neu: Seli Bau GmbH in Liquidation. "
                "Mit Urteil vom 28.08.2018 hat der Konkursrichter des Bezirksgerichts Uster "
                "über die Gesellschaft mit Wirkung ab dem 28.08.2018 den Konkurs eröffnet."
            ),
        },
    )
    analysis.run_aggregate(conn)
    case = db.get_case(conn, "uid:CHE-342.219.250:BANKRUPTCY")
    assert case["opened_date"] == "2018-08-28"  # not the stale 2014-05-22 reference date


def test_force_reanalyze_rebuilds_stale_case_fields(conn):
    """A heuristic fix must actually overwrite previously (wrongly) aggregated
    fields on --force, not just merge forward with COALESCE."""
    raw = {
        "publication_id": "pub-1",
        "publication_date": "2018-08-28",
        "uid": "CHE-342.219.250",
        "company_block_text": "Seli Bau GmbH",
        "canton": "ZH",
        "category": "Commercial Registry entries",
        "subcategory": "Change",
        "title": "title",
        "body_text": "Konkurs eröffnet. Datum 01.01.2099.",
    }
    db.upsert_publication_raw(conn, raw)
    analysis.run_aggregate(conn)
    case = db.get_case(conn, "uid:CHE-342.219.250:BANKRUPTCY")
    assert case["opened_date"] == "2099-01-01"

    # Simulate a heuristic fix changing the extracted date, then force-rebuild.
    raw["body_text"] = "Konkurs eröffnet. Datum 02.02.2000."
    db.upsert_publication_raw(conn, raw)
    analysis.run_aggregate(conn, force=True)
    case = db.get_case(conn, "uid:CHE-342.219.250:BANKRUPTCY")
    assert case["opened_date"] == "2000-02-02"
