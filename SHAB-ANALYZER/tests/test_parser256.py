from pathlib import Path

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import extract_persons, extract_text_extras, map_hr_xml, parse_publication_xml
from shab_analyzer.parser256 import extract_parser256_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('18f580bf', 'de.text.other_address_deleted_supplement.v1', 1),
    ('38ab3ec1', 'fr.persons.partial_share_transfer_new_collective_manager.v1', 2),
    ('6f76e261', 'fr.persons.council_replacement_vice_president_typo.v1', 8),
    ('70e16c63', 'de.text.covered_bond_creditor_deed_filed.v1', 6),
    ('7f76f193', 'fr.persons.board_president_collective_signing_grammar.v1', 2),
    ('83afc884', 'de.text.foundation_asset_transfer_investment_claims.v1', 1),
    ('99a04d75', 'de.persons.board_manager_residence_typo.v1', 1),
    ('a490b3c6', 'de.text.auditor_appointed_waiver_deleted.v1', 2),
    ('b286c021', 'de.text.full_address_collective_proxy_replacement.v1', 3),
    ('d637792f', 'de.text.provisional_moratorium_extended_struck_clause.v1', 1),
    ('e1387431', 'fr.persons.two_residences_one_origin_changed.v1', 2),
    ('f7ee690a', 'fr.persons.limited_partnership_amounts_role_changed.v1', 3),
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
    return leftover, context


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    result = parse_publication_xml(path(prefix))
    assert PARSER_VERSION == 256
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = selected(prefix)
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    leftover, context = residual(prefix)
    changed = leftover + '. UNRECOGNIZED_SUFFIX'
    assert extract_parser256_leftovers(changed, *context) == ([], changed)


@pytest.mark.parametrize('old,new', [('cède 98', 'cède 99'), ('102 parts', '103 parts'), ('102 parts de CHF 100', '102 parts de CHF 200')])
def test_inconsistent_transfer_preserved(old, new):
    leftover, context = residual('38ab3ec1')
    assert old in leftover
    changed = leftover.replace(old, new)
    assert extract_parser256_leftovers(changed, *context) == ([], changed)


def test_payloads():
    address = selected('18f580bf')[0].payload
    assert address['action'] == 'deleted' and address['notice_date'] == '2020-01-14'
    seller, buyer = selected('38ab3ec1')
    assert seller.payload['shares_before'] == 200
    assert seller.payload['shares_count'] == 102
    assert seller.payload['shares_transferred'] == buyer.payload['shares_received'] == 98
    assert seller.signing is None and buyer.signing == 'Kollektivunterschrift zu zweien'
    council = selected('6f76e261')
    assert all(e.payload['signing_revoked'] and e.signing is None for e in council[:3])
    assert council[3].role == 'vice-présidente du conseil'
    assert council[4].payload['previous_role'] == 'vice-président'
    assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in council[3:])
    assert council[5].payload['place'] == 'Carouge (GE)'
    bonds = selected('70e16c63')
    assert len({e.payload['isin'] for e in bonds}) == 6
    assert bonds[0].payload['rate'] == '0.375' and bonds[-1].payload['maturity'] == '2034-12-04'
    assert all(e.payload['filed'] == '2020-01-23' for e in bonds)
    transfer = selected('83afc884')[0].payload
    assert transfer['assets'] == "20'592'557.00" and transfer['claims'] == "191'484.39"
    assert transfer['value'] == '107.5417' and transfer['nav_date'] == '2019-11-29'
    auditor, waiver = selected('a490b3c6')
    assert auditor.person_key == 'uid:CHE-107.424.608'
    assert auditor.event_type == waiver.event_type == 'auditor_changed'
    assert waiver.payload['action'] == 'deleted' and waiver.payload['declaration_date'] == '2017-03-17'
    address, old, new = selected('b286c021')
    assert address.payload['postal_code'] == '3185'
    assert old.signing is None and old.payload['signing_revoked'] is True
    assert new.signing == 'Kollektivprokura zu zweien'
    moratorium = selected('d637792f')[0].payload
    assert moratorium['definitive'] is False
    assert moratorium['previous_until'] == '2020-02-04' and moratorium['until'] == '2020-03-04'
    first, second = selected('e1387431')
    assert first.payload['origin'] == 'Bussigny' and 'origin' not in second.payload
    amounts = selected('f7ee690a')
    assert amounts[0].payload['previous_amount'] == "10'000'000"
    assert amounts[0].payload['amount'] == "7'500'000"
    assert amounts[2].payload['signing_revoked'] is True and amounts[2].signing is None
    assert amounts[2].role == 'associé commanditaire'
    assert selected('99a04d75')[0].payload['place'] == 'Saint-Aubin FR'
    assert selected('7f76f193')[1].role == 'administrateur président'


@pytest.mark.parametrize('prefix,old,new', [
    ('d637792f', 'Verfügung vom 04.11.2019', 'Verfügung vom 05.11.2019'),
    ('83afc884', 'Anlagegruppe Immobilien Schweiz', 'Anlagegruppe UNRECOGNIZED'),
    ('7f76f193', 'les pouvoirs de Stocker Peter', 'les pouvoirs de UNRECOGNIZED'),
])
def test_inconsistent_context_preserved(prefix, old, new):
    leftover, context = residual(prefix)
    assert old in leftover
    changed = leftover.replace(old, new)
    assert extract_parser256_leftovers(changed, *context) == ([], changed)
