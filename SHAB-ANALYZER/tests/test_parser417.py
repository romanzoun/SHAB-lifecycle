import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser417 import extract_parser417_leftovers as extract, _LEGACY

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['04cb8da61a6a6627861a1622f2cd5435afc3c03738ee82bf7c4fe40e1404d6f4', '1982ae376d2d27c26354cdcbdfe0bebe1fe93ab9580bf49935d20ae62e39dbe2', '208002d935ddb480f097ef48ccf74bf2c0326777e32da6c487e066901b783c6d', '33893faf92b95774e9476b082990dcdacd0900e0024f938ee0e27669160e6f01', '3bd8b94e636997271d1b50483f3d02ed7e4c4c73e3a689380fc07170ceca702b', '63abe1f925aedd4a7f1b01c9c1ad09f0736cfe84d8e26ff204a83d4e23f26b61', '9367840aec067c52ba6de025213f12b2cd710c37ad22b899c575800142a80b02', 'a1646903d8a2684592404e926d97a9f19275f7037d6759ea3afd6115af6914d4', 'a6b80a4059207964958dc554d25eef80dff6049e609c52c0eac67aef91c8bbb3', 'a8ab9cfe47582c485e1118bb01aed7f1ae630e4f330ce3ee1047bd1f11446621', 'dc4ed1a4545fd192f16595eac89d8a27e83ec8b6719eaeafdf0402d1aea4b48a', 'e483f9a3b8d329603acfe77638f20d7a76141c0c88e52878433ecec758a45e0a']
COUNTS = [2, 1, 1, 1, 1, 1, 1, 3, 2, 2, 1, 2]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser417_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser417_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 444
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', range(12))
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', range(12))
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    if index == 8:
        assert (events, rest) == ([], args[0])
    else:
        assert len(events) == COUNTS[index] and rest == ''


EXPECTED = [
 ('ownership_changed', {'count':'6', 'before':'175', 'remaining':'169'}),
 ('status_changed', {'decision_date':'01.02.2021', 'effective_date':'01.02.2021'}),
 ('organization_changed', {'place':'Klosters'}),
 ('organization_changed', {'entry':'1172', 'auditor_uid':'CHE-102.360.639', 'corrected':True}),
 ('organization_changed', {'previous_head_office_id':'CH-020.4.046-946-1', 'historical_annotation':True}),
 ('organization_changed', {'reason':'Anpassung des Sitzes infolge Namensänderung der Gemeinde'}),
 ('organization_changed', {'entered_date':'10.02.2021', 'correct_date':'10.12.2020', 'corrected':True}),
 ('ownership_changed', {'count1':'66', 'count2':'66', 'before':'200', 'remaining':'68'}),
 ('officer_changed', {'excluded_between_appointees':True}),
 (None, {}),
 ('officer_changed', {'procuration_revoked':True}),
 ('officer_changed', {'origin':'La Tour-de-Peilz'}),
]


@pytest.mark.parametrize('index', range(12))
def test_semantics(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    kind, fields = EXPECTED[index]
    assert rest == ''
    if kind:
        assert events[0].event_type == kind
    for key, value in fields.items():
        assert events[0].payload[key] == value
    if index in (0, 7):
        assert all(e.signing == 'ohne Zeichnungsberechtigung' for e in events[1:])
    if index == 8:
        assert all(e.signing == 'Kollektivunterschrift zu zweien' for e in events)
        assert len(events[0].payload['excluded_partners']) == 4
        assert extract(*args, source_text='') == ([], args[0])
    if index == 9:
        from shab_analyzer.parser90 import extract_parser90_leftovers
        clause = args[0].split('. Abspaltung: ', 1)[0] + '.'
        expected, remainder = extract_parser90_leftovers(clause, *args[1:])
        assert remainder.strip(' .') == '' and events[:1] == expected
        assert 'assets' not in events[0].payload
        assert events[1].payload['assets'] == "14'634'815"
        assert events[1].payload['liabilities'] == "14'634'804"
        assert events[1].payload['capital_increase'] is False
    if index == 10:
        assert events[0].role == 'sous-directeur'
        assert events[0].signing == 'Kollektivunterschrift zu zweien'
    if index == 11:
        assert all(e.signing == 'Kollektivprokura zu zweien' for e in events)
        assert [e.payload['place'] for e in events] == ['Saint-Prex', 'Préverenges']


LEGACY_TEXTS = [
 'Als Statutendatum wurde irrtümlich 10.02.2021 anstelle von 10.12.2020 eingetragen.',
 "Signature collective à deux, avec l'administrateur ou le directeur, a été conférée à Test Anna, nommé sous-directeur; sa procuration est radiée.",
 'Abspaltung: Ein Teil der Aktiven und Passiven geht gemäss Spaltungsvertrag vom 22.01.2021 auf die Test GmbH, in Luzern (CHE-107.374.778), über.',
]


@pytest.mark.parametrize('pattern,text', list(zip(_LEGACY, LEGACY_TEXTS)))
def test_old_rule_boundaries_without_active_old_rules(pattern, text):
    assert pattern.fullmatch(text)
    assert extract(text, 'fr' if text.startswith('Signature') else 'de', 'p', '', None, None, None, source_text=text) == ([], text)


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name':'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name':'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index,before,after', [(0, 'de ses 175 parts', 'de ses 176 parts'), (7, 'de ses 200 parts', 'de ses 201 parts')])
def test_inconsistent_transfer_totals(index, before, after):
    _, _, (args, kwargs) = captured(index)
    changed = args[0].replace(before, after)
    assert changed != args[0]
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
