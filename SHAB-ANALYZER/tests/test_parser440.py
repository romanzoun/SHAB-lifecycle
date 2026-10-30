import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser440 import extract_parser440_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '113d12e745eb185d3973cc959412a5ce52d03c4f6be7d05fe1b5c5a9bfd4ba50', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2910a5545fe3b1246f679f1e20f68ecb139de892e702beac38b315f956ef13f8', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3c5b4c9dd0d450e36dc13561aff9453ec38255a6b178e8a0a880f9bcc76580c1', '87a23376e260a243fa3b69d4d7be7a4bddb12ffd8ff46281f3bb88b8206b5442', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '93cdf44ef87d12ef0f9de2a5a0051a0d4a3a73f6c41b4941855872ae8ce7aefd', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'e9e2e9866ecae45b95b1f04fd8ff56d95a3b5fff441dc6e2ad2875e296dd14b0', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser440_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser440_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 440
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
    if index == 10:
        assert events == [] and rest == args[0]
    else:
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
        if not name.startswith('extract_parser') or name == 'extract_parser440_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index,owner', [(0, 60), (2, 55), (4, 55), (7, 55), (9, 60), (11, 55)])
def test_existing_formulations_retain_historical_ownership(index, owner):
    import importlib
    result, old, (args, kwargs) = captured(index)
    old_extract = getattr(importlib.import_module(f'shab_analyzer.parser{owner}'), f'extract_parser{owner}_leftovers')
    owned_args = (kwargs['source_text'], *args[1:]) if index == 7 else args
    expected = old_extract(*owned_args)
    assert expected[0] or expected[1] != owned_args[0]
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old
    assert result.status == 'PARTIALLY_PARSED'
    assert old_extract(*owned_args) == expected




@pytest.mark.parametrize('index,event_type,expected', [
    (1, 'organization_changed', {'previous_identifier': 'CH-217-3531050-5', 'uid': 'CHE-110.573.048'}),
    (3, 'capital_changed', {'count': '100', 'profit_right': True, 'liquidation_surplus_right': True}),
    (5, 'capital_changed', {'statutes_date': '02.03.2021', 'fully_paid': True, 'shareholder_communication_deleted': True, 'previous_share_kind': 'au porteur'}),
    (6, 'capital_changed', {'count': '98', 'previous_count': '198', 'name': 'Magnin John Alexandre Sinclair'}),
    (8, 'organization_changed', {'agreement_date': '25.11.2020', 'amendment_date': '05.02.2021', 'assets': "100'000", 'consideration': '1'}),
    (10, 'status_changed', {'day': '28', 'month': 'janvier', 'year': '2021', 'dissolved': True, 'bankruptcy_liquidation': True}),
])
def test_evidenced_semantics(index, event_type, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == event_type
    for key, value in expected.items():
        assert events[0].payload[key] == value
    if index == 8:
        assert 'liabilities' not in events[0].payload
    if index == 10:
        assert events[0].payload['english_name'].endswith('Ltd liab. Co in liquidation')


def test_dissolution_requires_source_and_valid_written_date():
    _, _, (args, kwargs) = captured(10)
    assert extract(*args, source_text='unrelated') == ([], args[0])
    text = args[0].replace('28 janvier', '32 janvier')
    assert extract(text, *args[1:], source_text=kwargs['source_text'].replace('28 janvier', '32 janvier')) == ([], text)
