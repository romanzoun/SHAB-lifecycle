import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser303 import extract_parser303_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0b2139d8', 'fr.text.domicile_locality_corrected.v1', 1),
    ('17d341b7', 'de.text.proprietor_bankruptcy_appeal_suspended.v1', 1),
    ('3941591a', 'de.text.association_dissolved_corporate_liquidator.v1', 1),
    ('46f2823a', 'fr.text.administrator_presidency_corrected.v1', 1),
    ('51b84c40', 'fr.text.corporate_associate_name_completed.v1', 1),
    ('7b145d61', 'fr.text.contribution_and_communication_clauses_deleted.v1', 1),
    ('8045805f', 'de.text.reinstatement_liquidation_details_retained.v1', 1),
    ('b0d2e4df', 'de.text.early_deletion_tax_consent_pending.v1', 1),
    ('de2fbbeb', 'fr.text.associate_manager_transfer_presidency.v1', 3),
    ('dfafca40', 'de.text.company_name_share_conversion_corrected.v1', 1),
    ('e50a4bb8', 'de.text.partial_assets_transferred_without_consideration.v1', 1),
    ('fb362dd7', 'fr.text.two_associates_transfer_new_manager.v1', 2),
]


def path(prefix):
    paths = list(FIXTURES.glob(prefix + '*.xml'))
    assert len(paths) == 1
    return paths[0]


def selected(prefix):
    rule = next(rule for stem, rule, _ in CASES if stem == prefix)
    return [e for e in parse_publication_xml(path(prefix)).events if e.rule_id == rule]


def invocation(prefix):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract_parser303_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser303_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 303
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    events = [e for e in result.events if e.rule_id == rule]
    assert len(events) == count
    assert all(e.publication_id == result.publication_id and e.org_uid == result.org_uid for e in events)
    if any(e.signing for e in events):
        assert not any(e.rule_id == 'fr.persons.group_signing.v1' for e in result.events)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_unknown_suffix_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract_parser303_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser303_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])




@pytest.mark.parametrize('prefix', ['0b2139d8', '17d341b7', '3941591a', '46f2823a', '51b84c40', '8045805f', 'b0d2e4df', 'dfafca40', 'e50a4bb8'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser303_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('old,new', [('13. März', '32. März'), ('21. März', '32. März')])
def test_invalid_written_dates_preserved(old, new):
    args, kwargs = invocation('dfafca40')
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser303_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('de2fbbeb', 'signature individuelle', 'signature inconnue'),
    ('fb362dd7', 'signature collective à deux', 'signature inconnue'),
    ('46f2823a', 'collectivement à deux', 'individuellement'),
    ('de2fbbeb', 'cède 100', 'cède 101'),
    ('fb362dd7', 'chacun 25', 'chacun 26'),
])
def test_unsupported_or_inconsistent_transfer_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser303_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    locality = selected('0b2139d8')[0].payload
    assert locality['place'] == 'Aïre' and locality['previous_place'] == 'Aire'
    bankruptcy = selected('17d341b7')[0].payload
    assert bankruptcy['decision_date'] == '14.05.2020' and bankruptcy['time'] == '11.00'
    assert selected('3941591a')[0].payload['uid'] == 'CHE-112.589.333'
    officer = selected('46f2823a')[0]
    assert officer.signing == 'Kollektivunterschrift zu zweien'
    assert officer.payload['removed_role'] == 'président'
    assert len(officer.payload['signing_partners']) == 2
    associate = selected('51b84c40')[0].payload
    assert associate['name'] != associate['previous_name'] and associate['uid'] == 'CHE-383.671.618'
    assert selected('7b145d61')[0].payload['action'] == 'contribution_and_communication_clauses_deleted'
    assert selected('8045805f')[0].payload['decision_date'] == '20.04.2020'
    assert selected('b0d2e4df')[0].payload['confirmation_date'] == '27.01.2020'
    transfer, president, buyer = selected('de2fbbeb')
    assert transfer.payload['before'] == '200' and transfer.payload['remaining'] == '100'
    assert president.role == 'associé-gérant, président'
    assert buyer.signing == 'Einzelunterschrift' and buyer.payload['origin'] == 'Bosnie et Herzégovine'
    capital = selected('dfafca40')[0].payload
    assert capital['capital'] == "600'000" and capital['a_count'] == '450' and capital['b_count'] == '150'
    assert capital['name'] != capital['previous_name']
    assets = selected('e50a4bb8')[0].payload
    assert assets['assets'] == "624'548.35" and assets['liabilities'] == "142'000.00"
    transfer, buyer = selected('fb362dd7')
    assert transfer.payload['each'] == '25' and transfer.payload['buyer_count'] == '50'
    assert buyer.role == 'associé, gérant' and buyer.signing == 'Kollektivunterschrift zu zweien'
