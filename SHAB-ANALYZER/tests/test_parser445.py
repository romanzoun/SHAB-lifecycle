import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser445 import extract_parser445_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '4c9eb004b015d4eb1a9e4d305c9be7bb8e9be696628fcdf81774b8ec782cc5c5', '883838596e2377d9c6bddaad4302a94da280f6c38a6217ca51cdc97a57d1305b', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', '919be45dedc66824c21481cd5c22e3e97612130865558b52993563632b8e5b73', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser445_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser445_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 445
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
        if not name.startswith('extract_parser') or name == 'extract_parser445_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [0, 1, 2, 3, 6, 7, 9, 10, 11])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old



def test_legacy_transfer_pattern_deferred_without_old_parser():
    from shab_analyzer.parser101 import _FR_ASSET_TRANSFER_DUPLICATE_CURRENCY, extract_parser101_leftovers
    _, _, (args, kwargs) = captured(4)
    text = args[0].replace(" à Romande", ", à Romande")
    assert _FR_ASSET_TRANSFER_DUPLICATE_CURRENCY.search(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser101_leftovers(text, *args[1:])
    assert events and rest == ''
    assert events[0].event_type == 'assets_transferred'


@pytest.mark.parametrize('index,event_type,expected', [
    (4, 'assets_transferred', {'date': '2020-01-25', 'assets': "35'708'182", 'liabilities': "1'003'000", 'consideration': "34'705'182", 'recipient_uid': 'CHE-105.952.948'}),
    (5, 'legal_form_changed', {'entry': '22910', 'correction': True, 'social_parts_issued': 360, 'social_part_nominal': '100', 'previous_nominal': "1'000", 'transformation_plan_date': '2020-12-02', 'balance_sheet_date': '2020-11-30'}),
    (8, 'capital_changed', {'count': 60, 'nominal': "1'000", 'previous_kind': 'au porteur', 'share_kind': 'nominatives'}),
])
def test_evidenced_semantics(index, event_type, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and events[0].event_type == event_type
    assert events[0].payload.items() >= expected.items()
    assert events[0].payload['currency'] == 'CHF'


def test_conversion_rejects_mismatched_count_and_nominal():
    _, _, (args, kwargs) = captured(8)
    for text in (args[0].replace('en 60', 'en 61'), args[0].replace("nominatives de CHF 1'000", "nominatives de CHF 100")):
        assert extract(text, *args[1:], **kwargs) == ([], text)


def test_invalid_hyphenated_entry_date_is_preserved():
    _, _, (args, kwargs) = captured(5)
    text = args[0].replace('21-12-2020', '31-02-2020')
    assert extract(text, *args[1:], **kwargs) == ([], text)


def test_unknown_language_preserves_original_whitespace():
    text = '  unsupported clause.  '
    assert extract(text, None, 'p', '', None, None, None) == ([], text)
