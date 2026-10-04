from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser257 import extract_parser257_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0ba87790', 'de.text.authorized_participation_capital_increase.v1', 1),
    ('4c5d266e', 'fr.text.bankruptcy_suspensive_effect_january.v1', 1),
    ('4fe4ae7e', 'fr.persons.two_directors_promoted_collective_signing.v1', 2),
    ('73df54c7', 'fr.persons.two_partial_share_transfers_new_manager.v1', 3),
    ('7d1c112c', 'fr.text.foundation_asset_transfer_two_contract_dates.v1', 1),
    ('83f1f318', 'de.persons.executive_member_new_or_changed.v1', 1),
    ('85ae18bf', 'de.text.branch_deleted.v1', 1),
    ('85b8d49c', 'de.text.composition_moratorium_months_granted.v1', 1),
    ('9d3dc6a8', 'fr.persons.residence_corrected_notice_typo.v1', 1),
    ('a37ed41b', 'fr.persons.board_president_appointed_liquidator.v1', 2),
    ('d11c8e74', 'fr.persons.manager_and_corporate_liquidators.v1', 2),
    ('ea9de20e', 'de.text.branch_struck_from_new_listing.v1', 1),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def residual(prefix):
    p = path(prefix)
    meta, xml_events, text = map_hr_xml(p)
    context = (meta.get('language'), meta.get('publication_id') or p.stem,
               meta.get('published_at') or '', meta.get('org_uid'), meta.get('plz'), meta.get('canton'))
    persons, leftover = extract_persons(text, *context)
    _, leftover = extract_text_extras(leftover, *context, {e.event_type for e in xml_events + persons})
    return leftover, context, text


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    result = parse_publication_xml(path(prefix))
    assert PARSER_VERSION >= 257
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    leftover, context, text = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser257_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('old,new', [('chacun 13', 'chacun 14'), ('avec 26 parts', 'avec 27 parts'), ('de 64 et 65', 'de 64 et 66'), ('26 parts de CHF 100', '26 parts de CHF 200')])
def test_inconsistent_shares_preserved(old, new):
    leftover, context, text = residual('73df54c7')
    assert old in leftover
    changed = leftover.replace(old, new)
    assert extract_parser257_leftovers(changed, *context, source_text=text) == ([], changed)


@pytest.mark.parametrize('prefix', ['73df54c7', 'a37ed41b'])
def test_signing_requires_source_evidence(prefix):
    leftover, context, _ = residual(prefix)
    assert extract_parser257_leftovers(leftover, *context) == ([], leftover)


def test_payloads():
    capital = selected('0ba87790')[0].payload
    assert capital['date'] == '2019-12-23' and capital['statutes_article'] == 'Art. 3a'
    assert 'amount' not in capital
    assert selected('4c5d266e')[0].payload['decision_date'] == '2020-01-16'
    first, second = selected('4fe4ae7e')
    assert first.role == 'directeur' and first.payload['previous_role'] == 'directeur adjoint'
    assert second.role == 'directrice' and second.payload['place'] == 'Veyrier'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in (first, second))
    a, b, buyer = selected('73df54c7')
    assert [a.payload['shares_count'], b.payload['shares_count']] == [64, 65]
    assert [a.payload['shares_before'], b.payload['shares_before']] == [77, 78]
    assert a.payload['shares_transferred'] + b.payload['shares_transferred'] == buyer.payload['shares_received'] == 26
    assert a.signing is None and b.signing is None
    assert buyer.signing == 'Kollektivunterschrift zu zweien'
    assert buyer.payload['place'] == 'Londres (Royaune-Uni)'
    transfer = selected('7d1c112c')[0].payload
    assert transfer['date'] == '2019-11-28' and transfer['second_date'] == '2019-12-10'
    assert transfer['approval_date'] == '2020-01-06'
    assert transfer['assets'] == transfer['consideration'] == "4'175'000"
    assert transfer['property_number'] == '3308' and transfer['uid'] == 'CHE-112.607.310'
    executive = selected('83f1f318')[0]
    assert executive.role == 'Mitglied der Geschäftsleitung'
    assert executive.payload['place'] == 'Meilen' and executive.payload['action'] == 'new_or_changed'
    assert executive.signing == 'Kollektivunterschrift zu zweien'
    assert selected('85ae18bf')[0].payload['uid'] == 'CHE-441.228.962'
    moratorium = selected('85b8d49c')[0].payload
    assert moratorium['duration_months'] == 6 and moratorium['decision_date'] == '2020-01-13'
    assert 'until' not in moratorium and 'definitive' not in moratorium
    correction = selected('9d3dc6a8')[0].payload
    assert correction['place'] == 'Huntington (USA)' and correction['previous_place'] == 'New York (USA)'
    assert correction['notice_ref'] == '0/1004794209'
    assert selected('a37ed41b')[0].signing == 'Einzelunterschrift'
    manager, corporate = selected('d11c8e74')
    assert manager.role == corporate.role == 'liquidateur'
    assert manager.signing == 'Einzelunterschrift' and corporate.signing is None
    assert corporate.person_key == 'uid:CHE-331.113.877'
    branch = selected('ea9de20e')[0].payload
    assert branch['action'] == 'deleted' and branch['registry_canton'] == 'VD'


@pytest.mark.parametrize('prefix,old', [('73df54c7', 'signature collective à deux'), ('a37ed41b', 'signature individuelle')])
def test_unknown_signing_preserved(prefix, old):
    leftover, context, text = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, 'UNRECOGNIZED_SIGNING')
    assert extract_parser257_leftovers(changed, *context, source_text=text) == ([], changed)
