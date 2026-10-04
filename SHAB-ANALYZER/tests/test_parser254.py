from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser254 import extract_parser254_leftovers

FIXTURES = Path(__file__).parent / "fixtures"
CASES = [
    ("17e91519", "fr.persons.two_managers_liquidators.v1", 2),
    ("1ed38f50", "fr.text.foundation_asset_transfer.v1", 1),
    ("2170a25e", "fr.text.bankruptcy_appeal_suspensive_effect.v1", 1),
    ("3f1fbff0", "fr.persons.associate_manager_origin_residence_corrected.v1", 1),
    ("456645a7", "fr.persons.administrator_given_name_corrected_notice.v1", 1),
    ("57694ed0", "fr.text.branch_seat_changed.v1", 1),
    ("91352eff", "fr.persons.five_liquidators_individual_signing.v1", 5),
    ("b5be198d", "de.text.foundation_deed_date_purpose_reservation_corrected.v1", 2),
    ("dd1f306b", "fr.persons.committee_president_signing_transition.v1", 2),
    ("f360eda3", "de.text.authorized_capital_increase_offset_claims.v1", 1),
    ("f4376fa2", "fr.persons.board_membership_denied_signing_retained.v1", 1),
    ("f659df76", "fr.persons.two_associates_transfer_to_five_unsigned_associates.v1", 7),
]


def parse(prefix):
    paths = list(FIXTURES.glob(f"{prefix}*.xml"))
    assert len(paths) == 1
    return parse_publication_xml(paths[0])


def events(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse(prefix).events if e.rule_id == rule]


@pytest.mark.parametrize("prefix,rule,count", CASES)
def test_samples_fully_parsed(prefix, rule, count):
    result = parse(prefix)
    assert PARSER_VERSION >= 254
    assert result.sub_rubric == "HR02"
    assert result.status == "FULLY_PARSED"
    assert result.leftover_text == ""
    selected = [e for e in result.events if e.rule_id == rule]
    assert len(selected) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in selected)


def test_financial_and_branch_payloads():
    transfer = events("1ed38f50")[0].payload
    assert transfer["agreement_date"] == "2019-05-21"
    assert transfer["decision_date"] == "2019-10-01"
    assert transfer["assets"] == "127'977.75"
    assert transfer["liabilities"] == "56'177.75"
    assert transfer["recipient_uid"] == "CHE-106.080.021"
    assert transfer["consideration"] == "none"
    capital = events("f360eda3")[0].payload
    assert capital["claims_count"] == 24
    assert capital["offset_amount"] == "4'246'000.00"
    assert capital["shares_count"] == 1061500
    assert capital["shares_nominal"] == "0.10"
    branch = events("57694ed0")[0].payload
    assert branch["branch_uid"] == "CHE-132.247.114"
    assert branch["place"] == "Crissier"
    assert branch["previous_place"] == "Daillens"


def test_corrected_details_and_bankruptcy():
    corrected = events("3f1fbff0")[0]
    assert corrected.payload["origin"] == "Inde"
    assert corrected.payload["place"] == "Bengalore"
    assert corrected.payload["country"] == "IND"
    assert corrected.role == "associé-gérant"
    name = events("456645a7")[0].payload
    assert name["name"] == "Coletti Giordano"
    assert name["previous_name"] == "Coletti Giordani"
    assert name["notice_ref"] == "0/1004780917"
    board = events("f4376fa2")[0]
    assert board.payload["board_member"] is False
    assert board.role is None
    assert board.signing == "Kollektivunterschrift zu zweien"
    bankruptcy = events("2170a25e")[0].payload
    assert bankruptcy["decision_date"] == "2020-01-17"
    assert bankruptcy["bankruptcy_judgment_date"] == "2019-11-14"
    assert bankruptcy["action"] == "appeal_suspensive_effect_granted"


def test_liquidators_and_committee_signing():
    managers = events("17e91519")
    assert all(e.role == "gérant liquidateur" and e.payload["signing_unchanged"] for e in managers)
    assert all(e.signing == "Kollektivunterschrift zu zweien" for e in managers)
    liquidators = events("91352eff")
    assert all(e.person_key and e.signing == "Einzelunterschrift" for e in liquidators)
    assert sum(e.role == "administratrice liquidatrice" for e in liquidators) == 3
    president, former = events("dd1f306b")
    assert president.role == "président du comité"
    assert president.signing == "Kollektivunterschrift zu zweien"
    assert former.role == "membre du comité"
    assert former.signing is None
    assert former.payload["action"] == "signing_revoked"


def test_no_contradictory_foundation_reservation():
    result = parse("b5be198d")
    assert not any(e.rule_id == "de.text.purpose_reservation.v1" for e in result.events)
    date, reservation = events("b5be198d")
    assert date.payload["previous_date"] == "2010-09-30"
    assert reservation.payload["purpose_change_reserved"] is False
    assert any(e.payload.get("date") == "2010-11-17" for e in result.events)


def test_share_transfer_counts_without_invented_seller_allocation():
    selected = events("f659df76")
    sellers, buyers = selected[:2], selected[2:]
    assert all(e.payload["shares_count"] == 80 for e in sellers)
    assert all("shares_before" not in e.payload and "shares_transferred" not in e.payload for e in sellers)
    assert sum(e.payload["shares_received"] for e in buyers) == 40
    assert all(e.payload["shares_count"] == 8 and e.payload["without_signature"] for e in buyers)
    assert all(e.person_key and e.signing is None and e.payload["country"] == "F" for e in buyers)


@pytest.mark.parametrize("prefix,rule,count", CASES)
def test_unrelated_suffix_is_not_consumed(prefix, rule, count):
    # Use the actual supplied source, with an unrecognized suffix: no new XML data.
    from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml

    path = next(FIXTURES.glob(f"{prefix}*.xml"))
    meta, xml_events, text = map_hr_xml(path)
    context = (meta.get("language"), meta.get("publication_id") or path.stem,
               meta.get("published_at") or "", meta.get("org_uid"), meta.get("plz"), meta.get("canton"))
    person_events, leftover = extract_persons(text, *context)
    _, leftover = extract_text_extras(leftover, *context, {e.event_type for e in xml_events + person_events})
    unknown = leftover + " UNRECOGNIZED_SUFFIX"
    selected, remaining = extract_parser254_leftovers(unknown, *context)
    assert selected == []
    assert remaining == unknown


@pytest.mark.parametrize("prefix,old,new", [
    ("57694ed0", "Daillens (CHE-132.247.114)", "Daillens (CHE-132.247.115)"),
    ("f659df76", "cession de 40 parts", "cession de 41 parts"),
    ("f659df76", "chacun associé pour 8 parts de CHF 100", "chacun associé pour 8 parts de CHF 101"),
])
def test_inconsistent_branch_identity_or_share_totals_are_preserved(prefix, old, new):
    from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml

    path = next(FIXTURES.glob(f"{prefix}*.xml"))
    meta, xml_events, text = map_hr_xml(path)
    context = (meta.get("language"), meta.get("publication_id") or path.stem,
               meta.get("published_at") or "", meta.get("org_uid"), meta.get("plz"), meta.get("canton"))
    person_events, leftover = extract_persons(text, *context)
    _, leftover = extract_text_extras(leftover, *context, {e.event_type for e in xml_events + person_events})
    assert old in leftover
    inconsistent = leftover.replace(old, new)
    selected, remaining = extract_parser254_leftovers(inconsistent, *context)
    assert selected == []
    assert remaining == inconsistent
