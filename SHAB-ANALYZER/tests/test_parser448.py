import hashlib
import re
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser448 import extract_parser448_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed SHA-256 values supplied as the sample filenames, verified when copied.
SUPPLIED_SHA256 = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '384c2df3999d3936131f04916e6a38ac876aa6594f1c11fa88657884af3e1b8d', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '67f193f9b059b801cd9b32ac264221e9fa1f3a792f078199ffda828841cf13f4', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'ad2ac279b026e0be94729944b7ea9c5a668838405290cbed85a683060f3b6ac0', 'c32e1728bea4db2c46fc4b204cef6ab04e57b1d9cae0e1bce53c90ca1148470f', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']
COUNTS = [0, 0, 0, 0, 1, 0, 0, 0, 0, 3, 2, 0]
NEW_CASES = [i for i, count in enumerate(COUNTS) if count]


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (SUPPLIED_SHA256[index] + '.xml')
    with patch.object(parser, 'extract_parser448_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser448_leftovers', lambda text, *a, **kw: ([], text)):
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
    assert PARSER_VERSION == 547
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
        if not name.startswith('extract_parser') or name == 'extract_parser448_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        assert rest == args[0], name


@pytest.mark.parametrize('index', [0, 1, 2, 3, 5, 6, 7, 8, 11])
def test_existing_results_unchanged(index):
    result, old, (args, kwargs) = captured(index)
    assert extract(*args, **kwargs) == ([], args[0])
    assert result == old



@pytest.mark.parametrize('index,types,expected', [
    (4, ['officer_changed'], {'action': 'appointed', 'procuration_revoked': True}),
    (9, ['ownership_changed', 'officer_changed', 'officer_changed'], {'count': '10', 'before': '20', 'remaining': '10', 'currency': 'CHF'}),
    (10, ['ownership_changed', 'officer_changed'], {'count': '10', 'before': '20', 'remaining': '10', 'currency': 'CHF'}),
])
def test_evidenced_semantics(index, types, expected):
    _, _, (args, kwargs) = captured(index)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    assert [e.event_type for e in events] == types
    assert events[0].payload.items() >= expected.items()
    if index == 9:
        assert events[1].role == 'associé-gérant' and events[1].signing is None
        assert events[2].role == 'président' and events[2].signing is None
    if index == 10:
        assert events[1].role == 'associée'
        assert events[1].signing == 'ohne Zeichnungsberechtigung'

@pytest.mark.parametrize('index', [9, 10])
def test_reject_inconsistent_holding(index):
    _, _, (args, kwargs) = captured(index)
    changed = args[0].replace('de ses 20 parts', 'de ses 21 parts')
    assert extract(changed, *args[1:], **kwargs) == ([], changed)


def test_correct_spelling_still_owned_by_parser418():
    from shab_analyzer.parser418 import extract_parser418_leftovers
    _, _, (args, kwargs) = captured(10)
    text = args[0].replace('de et à Mies', 'de Mies, à Mies').replace('titutlaire', 'titulaire')
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser418_leftovers(text, *args[1:], **kwargs)
    assert len(events) == 2 and rest == ''


def test_legacy_presidency_deferred_using_original_pattern():
    from shab_analyzer.parser95 import _FR_SHARE_TRANSFER_AND_PRESIDENCY, extract_parser95_leftovers
    _, _, (args, kwargs) = captured(9)
    text = args[0].replace('. Singh Jaspal', '; Singh Jaspal')
    assert _FR_SHARE_TRANSFER_AND_PRESIDENCY.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser95_leftovers(text, *args[1:])
    assert events and rest == ''


def test_legacy_manager_deferred_using_original_pattern():
    from shab_analyzer.parser85 import _FR_MANAGER_APPOINTED_PROXY_REVOKED, extract_parser85_leftovers
    _, _, (args, kwargs) = captured(4)
    text = args[0].replace("membre et président du conseil d'administration", 'gérant')
    assert _FR_MANAGER_APPOINTED_PROXY_REVOKED.fullmatch(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    events, rest = extract_parser85_leftovers(text, *args[1:])
    assert events and rest == ''
