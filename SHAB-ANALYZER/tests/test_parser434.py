import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser434 import extract_parser434_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '0a923c30a4531ceb2d33e1d6e6e3e7bc519e57f3cbddb5fe3b28d057511d12c1', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '42b539651ea24efea23ce14180914af62cc6aa4f6dcd22e8eb2f390dd7b0cffc', '6d42b4f3841f1392da8d5645d5160d638bfe96f107dcabf8fe86f6d1fba0ca9a', '8390a963aae8357989618aa293183787edcc90e4dd79e0e0356b3bcc27552f2e', '92df0b0eaa5084f46567c12e9aad679e93a6f2f7729aa0d0ea6a1a9283400beb', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'bba34ed7789de7512e38d0441aaa86562ad3c2c922bce0bab01a1aa3ea0e6414', 'e8cb57feff87be7d88db665b501a7af7478a305d6c48184e2f9aad5a1bd9d0c1', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed', 'fd5893798c86063979cc86794804a88256cc519ca31236c1aaca9f336dc7e72f']
COUNTS = [0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser434_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser434_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', SUPPLIED_SHA256)
def test_fixture_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', NEW_CASES)
def test_complete_and_unchanged_old_payloads(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    assert PARSER_VERSION == 446
    assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
    assert len(added) == COUNTS[index] and rest == ''
    assert old.leftover_text == args[0]
    assert result.events == old.events + added
    assert all(Event(**vars(e)) == e for e in added)


@pytest.mark.parametrize('index', NEW_CASES)
def test_unknown_suffix_language_and_invalid_dates(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0] + '. UNKNOWN_SUFFIX'
    assert extract(changed, *args[1:], **kwargs) == ([], changed)
    assert extract(args[0], 'en', *args[2:], **kwargs) == ([], args[0])
    for date in set(re.findall(r'\d{2}\.\d{2}\.\d{4}', args[0])):
        changed = args[0].replace(date, '31.02.2020')
        assert extract(changed, *args[1:], **kwargs) == ([], changed)


@pytest.mark.parametrize('index', NEW_CASES)
def test_missing_optional_metadata_and_source(index):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert len(events) == COUNTS[index] and rest == ''
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in events)
    events, rest = extract(*args)
    assert len(events) == COUNTS[index] and rest == ''


def test_old_event_without_optional_attributes():
    event = Event('p', '', 'officer_changed', 'legacy.rule', payload={'name': 'Test Anna'})
    assert Event(**vars(event)) == event
    assert event.payload == {'name': 'Test Anna'}
    assert event.role is None and event.signing is None


@pytest.mark.parametrize('index', NEW_CASES)
def test_no_overlap_with_old_rules_even_in_isolation(index):
    # Exercise every historical extractor on the complete clause in isolation.
    import inspect
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(index)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser434_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (2, 55), (7, 60), (10, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    expected = old_extract(*args)
    assert expected[0] or expected[1] != args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*args) == expected


@pytest.mark.parametrize('index,kind,action,expected', [
    (1, 'audit_requirement_changed', 'cooperative_board_declaration_audit_waiver', {'limited_audit_waived': True}),
    (3, 'capital_changed', 'capital_corrected_incomplete_entry_year', {'entry_date_text': '23.02.201', 'capital': "1'330'500", 'previous_capital': "13'305'000", 'fully_paid': True}),
    (4, 'status_changed', 'head_office_bankruptcy_branch_liquidation_name', {'scope': 'head_office', 'bankrupt': True, 'effective_time': '14h00'}),
    (5, 'status_changed', 'bankrupt_company_reinstated_court_order_old_law', {'reinstated': True, 'bankruptcy_reopened': True, 'procedure': 'summarisch'}),
    (6, 'officer_changed', 'branch_director_origin_signing_corrected', {'origin': 'France', 'corrected': True, 'previous_signing': 'Kollektivunterschrift zu zweien'}),
    (8, 'officer_changed', 'officer_domicile_corrected_signing_typo', {'place': 'Gibloux', 'previous_place': 'Bulle'}),
    (9, 'status_changed', 'official_deletion_cancelled_interest_typo', {'deletion_cancelled': True}),
    (11, 'officer_changed', 'officer_name_changed_typo_somme', {'previous_name': 'Ratini Roberto', 'name': 'Ratini Robert'}),
])
def test_evidenced_semantics(index, kind, action, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert events[0].event_type == kind
    assert events[0].rule_id == f'{args[1]}.text.{action}.v1'
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index in (6, 8):
        assert events[0].signing == ('Einzelunterschrift' if index == 6 else 'Kollektivunterschrift zu zweien')
