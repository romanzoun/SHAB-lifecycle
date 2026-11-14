import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser462 import extract_parser462_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed
f067fd551558e19694fa6fb0c44156022882bc1e621c94d36b4caa25aedfb2df'''.split()


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser462_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser462_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]


@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize('index', range(12))
def test_pipeline_preserves_existing_events(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 11:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_attributes():
    assert PARSER_VERSION == 551
    _, _, (args, kwargs) = captured(11)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'capital_changed'
    assert event.rule_id == 'fr.text.share_split_entry_complemented.v1'
    assert event.payload == {
        'kind': 'share_split',
        'split_from': {'count': 50, 'nominal': "1'000"},
        'split_to': {'count': 50000, 'nominal': '1'},
        'capital_total': "50'000", 'paid': "50'000", 'paid_in_full': True,
        'capital_count': 50000, 'capital_nominal': '1', 'share_kind': 'nominatives',
        'entry': '7146', 'entry_date': '2021-04-01',
    }
    optional, rest = extract(*args[:4], None, None, None)
    assert rest == '' and optional[0].payload == event.payload
    assert optional[0].org_uid is None and optional[0].plz is None and optional[0].canton is None
    legacy_payload = {k: v for k, v in event.payload.items() if k not in ('entry', 'entry_date')}
    legacy = Event('p', '', 'capital_changed', 'fr.text.share_split.v1', payload=legacy_payload)
    assert Event(**vars(legacy)) == legacy
    assert 'entry' not in legacy.payload and 'entry_date' not in legacy.payload
    assert extract(*args) == (events, '')


def test_invalid_and_unknown_inputs():
    _, _, (args, kwargs) = captured(11)
    for text in (args[0] + ' UNKNOWN', args[0].replace('01.04.2021', '31.02.2021'),
                 args[0].replace('les 50 actions', 'les 51 actions'),
                 args[0].replace('concurrence de CHF 50', 'concurrence de CHF 60'),
                 args[0].replace('7146', 'unknown')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:]) == ([], args[0])


def test_no_old_rule_consumes_new_formulation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(11)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser462_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_old_split_keeps_ownership():
    import shab_analyzer.parse as parser
    from shab_analyzer.parser58 import _FR_SHARE_SPLIT, extract_parser58_leftovers
    _, _, (args, _) = captured(11)
    text = ("Division des 50 actions de CHF 1'000, nominatives, en 50'000 actions de CHF 1, "
            "nominatives. Capital-actions: CHF 50'000, libéré à concurrence de CHF 50'000, "
            "divisé en 50'000 actions de CHF 1, nominatives")
    assert _FR_SHARE_SPLIT.fullmatch(text)
    assert extract_parser58_leftovers(text, *args[1:])[0]
    assert extract(text, *args[1:]) == ([], text)
    for index in range(12):
        if index != 11:
            result, baseline, _ = captured(index)
            assert result == baseline


@pytest.mark.parametrize('number,pattern,fixture', [
    (103, '_FR_REGISTERED_SHARE_SPLIT_FULLY_PAID', '666445a1-5f31-4ec5-b221-eb8776c5b7ef'),
    (119, '_FR_REGISTERED_SHARE_SPLIT_WITHOUT_SOURCE_KIND', '37a3ffc9-0f3b-47b3-bacd-1b40d851d8c0'),
    (247, '_FR_NOMINATIVE_SHARE_SPLIT', '5d529474-8721-4c02-86bc-5c6b4f386598'),
    (249, '_FR_NOMINATIVE_SHARE_SPLIT_UNRESTRICTED', '795c76b3-4515-47c6-8eea-c064bdabc05a'),
])
def test_legacy_deferred_and_pipeline_equal(number, pattern, fixture):
    import importlib
    import shab_analyzer.parse as parser
    module = importlib.import_module(f'shab_analyzer.parser{number}')
    # Exercise the old rule's own fixture corpus and exact regex, without
    # imposing a fixed overall status or remaining text on later parsers.
    matched = 0
    def capture(text, *args, **kwargs):
        nonlocal matched
        if getattr(module, pattern).search(text.strip()):
            matched += 1
            assert extract(text, *args, **kwargs) == ([], text)
        return original(text, *args, **kwargs)
    original = getattr(parser, f'extract_parser{number}_leftovers')
    for name in (fixture + '.xml',):
        with patch.object(parser, f'extract_parser{number}_leftovers', capture):
            result = parse_publication_xml(FIXTURES / name)
        with patch.object(parser, 'extract_parser462_leftovers', lambda text, *a, **kw: ([], text)):
            old = parse_publication_xml(FIXTURES / name)
        assert result == old
    assert matched

