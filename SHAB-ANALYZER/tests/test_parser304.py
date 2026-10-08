import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser304 import extract_parser304_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('16caa188', 'fr.text.procuration_individual_new_domicile.v1', 1),
    ('280bc323', 'de.text.no_registered_auditor.v1', 1),
    ('3b56e7ad', 'fr.text.audit_waiver_deleted_completion.v1', 1),
    ('5821c7ce', 'de.text.register_reference_year_corrected.v1', 1),
    ('5d4dcc8f', 'fr.text.reinstatement_summary_bankruptcy.v1', 1),
    ('5f6600eb', 'de.text.previous_notice_reference_corrected.v1', 1),
    ('62f69313', 'fr.text.collective_signing_restriction_removed.v1', 1),
    ('6e903ec0', 'it.text.authorized_conditional_capital_clauses.v1', 1),
    ('74813377', 'fr.text.management_member_elected_administrator.v1', 1),
    ('8fe5ec4d', 'fr.text.liquidator_name_address_corrected.v1', 2),
    ('c7ee7b5d', 'fr.text.three_administrators_signing_removed.v1', 3),
    ('fbd40092', 'de.text.assets_transfer_no_consideration.v1', 1),
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
        return extract_parser304_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser304_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 315
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
    assert extract_parser304_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser304_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix', ['3b56e7ad', '5821c7ce', '5d4dcc8f', '5f6600eb', '6e903ec0', '8fe5ec4d', 'fbd40092'])
def test_invalid_dates_preserved(prefix):
    import re
    args, kwargs = invocation(prefix)
    changed = re.sub(r'\d{2}\.\d{2}\.\d{4}', '31.02.2020', args[0], count=1)
    assert changed != args[0]
    assert extract_parser304_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,old,new', [
    ('16caa188', 'procuration individuelle', 'procuration collective à deux'),
    ('62f69313', 'sans restriction', 'avec restriction'),
    ('74813377', 'collectivement à deux', 'individuellement'),
    ('c7ee7b5d', "n'exercent plus", 'exercent'),
    ('fbd40092', 'Gegenleistung: keine', 'Gegenleistung: unbekannt'),
])
def test_unsupported_terms_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser304_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_payloads():
    assert selected('16caa188')[0].signing == 'Einzelprokura'
    assert selected('16caa188')[0].payload['place'] == 'Genève'
    assert selected('280bc323')[0].payload['action'] == 'no_registered_auditor'
    assert selected('3b56e7ad')[0].payload['entry'] == '913'
    assert selected('5821c7ce')[0].payload['year'] == '2020'
    assert selected('5d4dcc8f')[0].payload['second_date'] == '11.05.2020'
    assert selected('5f6600eb')[0].payload['correct_number'] == '73'
    assert selected('62f69313')[0].signing == 'Kollektivunterschrift zu zweien'
    capital = selected('6e903ec0')[0].payload
    assert capital['authorized_date'] == capital['conditional_date'] == '13.05.2020'
    assert capital['previous_first_date'] == '22.04.2016'
    officer = selected('74813377')[0]
    assert officer.role == 'administratrice' and officer.signing == 'Kollektivunterschrift zu zweien'
    correction, liquidator = selected('8fe5ec4d')
    assert correction.payload['name'] != correction.payload['previous_name']
    assert correction.payload['postal_code'] == '1110'
    assert liquidator.role == 'liquidateur'
    removed = selected('c7ee7b5d')
    assert len({e.person_key for e in removed}) == 3
    assert all(e.payload['signing_removed'] and e.signing == 'ohne Zeichnungsberechtigung' for e in removed)
    assets = selected('fbd40092')[0].payload
    assert assets['assets'] == "58'543.00" and assets['liabilities'] == "50'000.00"
    assert assets['uid'] == 'CHE-237.008.095'
