import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser453 import extract_parser453_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '16e569a7fc7f683457f19888b8e9865714f7aedd71360f8fd48d2f4ebfbbab41', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser453_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser453_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 468
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
    baseline, _ = extract(*args, **kwargs)
    assert [e.payload for e in events] == [e.payload for e in baseline]
    assert extract(*args) == extract(*args, **kwargs)


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
        if not name.startswith('extract_parser') or name == 'extract_parser453_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [i for i, count in enumerate(COUNTS) if not count])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old

def test_legacy_rule_owns_canonical_uid_and_payload_is_preserved():
    from shab_analyzer.parser155 import (
        _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY,
        extract_parser155_leftovers,
    )
    _, _, (args, kwargs) = captured(1)
    added, _ = extract(*args, **kwargs)
    raw_uid = added[0].payload['recipient_uid_raw']
    canonical = args[0].replace(raw_uid, raw_uid.replace("'", '.'))
    assert _DE_COMPANY_ASSET_TRANSFER_WITH_INVENTORY.fullmatch(canonical)
    assert extract(canonical, *args[1:], **kwargs) == ([], canonical)
    old_events, rest = extract_parser155_leftovers(canonical, *args[1:])
    assert rest == '' and len(old_events) == 1
    assert added[0].event_type == old_events[0].event_type == 'assets_transferred'
    assert added[0].payload == {**old_events[0].payload, 'recipient_uid_raw': raw_uid}
    assert old_events[0].rule_id == 'de.text.company_asset_transfer_with_inventory.v1'
    assert added[0].payload['agreement_date'] == '2021-03-18'
    assert added[0].payload['inventory_date'] == '2021-01-01'
    assert added[0].payload['assets'] == "5'746'424.35"
    assert added[0].payload['liabilities'] == "3'964'241.83"
    assert added[0].payload['consideration'] == "1'852'182.50"
    assert added[0].payload['recipient_uid'] == 'CHE-418.198.725'
    assert added[0].payload['recipient_canton'] is None
    # Existing records keep working without the new optional raw UID attribute.
    assert 'recipient_uid_raw' not in old_events[0].payload
    assert Event(**vars(old_events[0])) == old_events[0]


def test_unsupported_uid_punctuation_retains_input():
    _, _, (args, kwargs) = captured(1)
    events, _ = extract(*args, **kwargs)
    raw_uid = events[0].payload['recipient_uid_raw']
    for value in (raw_uid.replace("'", '-'), raw_uid.replace('.', "'")):
        changed = args[0].replace(raw_uid, value)
        assert extract(changed, *args[1:], **kwargs) == ([], changed)
