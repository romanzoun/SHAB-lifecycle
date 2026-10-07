import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser292 import extract_parser292_leftovers

FIXTURES = Path(__file__).parent / 'fixtures'
CASES = [
    ('0a9438dc', 'fr.persons.board_liquidators_individual.v1', 2),
    ('2830c841', 'de.text.conditional_capital_amended.v1', 1),
    ('2fdd287c', 'fr.text.branch_german_name_corrected.v1', 1),
    ('33697ec1', 'de.persons.board_roles_signing_name_corrected.v1', 4),
    ('426b9571', 'de.text.authorized_capital_two_decision_dates.v1', 1),
    ('43fa5b57', 'de.text.additional_address_foundation_name_removed.v1', 1),
    ('6d245f67', 'fr.persons.associate_manager_president_appointed.v1', 1),
    ('a657cc47', 'fr.persons.procuration_mutual_named_restrictions.v1', 2),
    ('b70127e0', 'fr.persons.partial_share_transfer_manager_president.v1', 3),
    ('be438eba', 'de.persons.corporate_associate_managers_shares_removed.v1', 3),
    ('e07f35e6', 'fr.text.associate_company_name_corrected.v1', 1),
    ('eb1fb82b', 'de.text.secondary_purpose_changed.v1', 1),
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
        return extract_parser292_leftovers(*args, **kwargs)
    with patch.object(parser, 'extract_parser292_leftovers', capture):
        parse_publication_xml(path(prefix))
    assert len(calls) == 1
    return calls[0]


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_fixture_complete(prefix, rule, count):
    p = path(prefix)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == p.stem
    result = parse_publication_xml(p)
    assert PARSER_VERSION == 299
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
    assert extract_parser292_leftovers(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('prefix,rule,count', CASES)
def test_wrong_language_preserved(prefix, rule, count):
    args, kwargs = invocation(prefix)
    assert extract_parser292_leftovers(args[0], 'en', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('prefix,old,new', [
    ('2830c841', '08.04.2020', '31.02.2020'),
    ('2830c841', '29.04.2015', '29.04.2021'),
    ('2fdd287c', '31.03.2020', '31.02.2020'),
    ('426b9571', '25.03.2020', '31.02.2020'),
    ('426b9571', '17.03.2020', '17.03.2021'),
    ('b70127e0', '154', '155'),
    ('b70127e0', 'CHF 100', 'CHF 0'),
    ('be438eba', '100 Stammanteilen', '101 Stammanteilen'),
    ('be438eba', '200.00', '0.00'),
    ('e07f35e6', '01.10.2019', '31.02.2019'),
])
def test_invalid_facts_preserved(prefix, old, new):
    args, kwargs = invocation(prefix)
    changed = args[0].replace(old, new)
    assert changed != args[0]
    assert extract_parser292_leftovers(changed, *args[1:], **kwargs) == ([], changed)


def test_fragment_requires_source():
    args, kwargs = invocation('426b9571')
    assert extract_parser292_leftovers(*args, source_text='') == ([], args[0])
    assert extract_parser292_leftovers(*args, source_text=kwargs['source_text'].replace('Statutenänderung: 17.03.2020', 'Statutenänderung: 18.03.2020')) == ([], args[0])


def test_payloads():
    assert all(e.signing == 'Einzelunterschrift' for e in selected('0a9438dc'))
    assert selected('2830c841')[0].payload['action'] == 'conditional_capital_amended'
    corrected = selected('2fdd287c')[0].payload
    assert corrected['translation'] != corrected['previous_translation']
    board = selected('33697ec1')
    assert board[0].role == 'Präsident des Verwaltungsrates'
    assert board[1].payload['previous_name'] != board[1].payload['name']
    assert board[2].signing == 'ohne Zeichnungsberechtigung' and board[3].role is None
    assert selected('426b9571')[0].payload['first_date'] == '17.03.2020'
    assert selected('43fa5b57')[0].payload['action'] == 'additional_address_name_removed'
    manager = selected('6d245f67')[0]
    assert manager.role == 'gérant président' and manager.signing == 'Einzelunterschrift'
    procuration = selected('a657cc47')
    for i, e in enumerate(procuration):
        assert e.signing == 'Kollektivprokura zu zweien'
        assert len(e.payload['excluded_signing_partners']) == 5
        assert procuration[1-i].payload['name'] in e.payload['excluded_signing_partners']
    transfer = selected('b70127e0')
    assert transfer[0].payload['transferred'] == '14' and transfer[0].payload['remaining'] == '154'
    assert transfer[1].signing == 'ohne Zeichnungsberechtigung'
    assert transfer[2].signing == 'Einzelunterschrift' and transfer[2].role == 'gérant président'
    corporate = selected('be438eba')
    assert corporate[0].payload['shares'] == '100' and corporate[0].payload['register_id'] == '11042276'
    assert all(e.payload['associate'] is False and e.signing == 'Einzelunterschrift' for e in corporate[1:])
    assert selected('e07f35e6')[0].payload['company'] != selected('e07f35e6')[0].payload['previous_company']
    assert selected('eb1fb82b')[0].payload == {'action': 'secondary_purpose_changed'}
