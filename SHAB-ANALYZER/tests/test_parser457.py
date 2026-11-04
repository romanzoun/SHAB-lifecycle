import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch
import pytest
from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser457 import extract_parser457_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
# Fixed supplied SHA-256 filenames, verified when copying; no job directory needed.
DIGESTS = '''02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11
1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e
31bc228c95a083db1a4f10db79c75cd34ab0f92b45004c2eb04de53cc4a8079d
3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232
7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad
7816e17662c0c95a623e05812bc2da3857f83485767632644a002c37b16ca32d
88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7
8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a
8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f
a341287297ba96e1938916b070b26a6384cd05b7aad34facefaf830c80dd6cf8
a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5
f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed'''.split()

@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser457_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser457_leftovers', lambda text, *a, **kw: ([], text)):
        old = parse_publication_xml(path)
    assert len(calls) == 1
    return result, old, calls[0]

@pytest.mark.parametrize('digest', DIGESTS)
def test_integrity(digest):
    assert hashlib.sha256((FIXTURES / (digest + '.xml')).read_bytes()).hexdigest() == digest

@pytest.mark.parametrize('index', range(12))
def test_pipeline_and_payload_preservation(index):
    result, old, (args, kwargs) = captured(index)
    added, rest = extract(*args, **kwargs)
    if index == 5:
        assert result.status == 'FULLY_PARSED' and result.leftover_text == ''
        assert len(added) == 1 and rest == ''
        assert result.events == old.events + added
    else:
        assert extract(*args, **kwargs) == ([], args[0])
        assert result == old

def test_exact_payload_and_version():
    assert PARSER_VERSION == 477
    _, _, (args, kwargs) = captured(5)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'capital_changed'
    assert event.rule_id == 'fr.text.registered_share_split_new_restrictions.v1'
    assert event.payload == {
        'kind': 'share_split', 'currency': 'CHF', 'from_count': 100,
        'from_nominal': "1'000", 'to_count': 100000, 'to_nominal': '1',
        'total': "100'000", 'fully_paid': True,
        'share_kind': 'actions nominatives', 'transfer_restricted': True,
    }
    assert Event(**vars(event)) == event


def test_missing_optional_fields_and_source():
    _, _, (args, kwargs) = captured(5)
    baseline, _ = extract(*args, **kwargs)
    events, rest = extract(*args[:4], None, None, None, **kwargs)
    assert rest == '' and len(events) == 1
    assert events[0].org_uid is None and events[0].plz is None and events[0].canton is None
    assert events[0].payload == baseline[0].payload
    assert extract(*args) == ([], args[0])
    legacy = Event('p', '', 'capital_changed', 'legacy.rule', payload={'kind': 'share_split'})
    assert Event(**vars(legacy)) == legacy
    assert legacy.payload == {'kind': 'share_split'}


def test_reject_unknown_and_inconsistent():
    _, _, (args, kwargs) = captured(5)
    for text in (args[0] + '; UNKNOWN', args[0].replace("CHF 100'000", 'CHF 999'),
                 args[0].replace("CHF 1'000", 'CHF 1..0'),
                 args[0].replace('100\'000 actions', '999 actions')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:], **kwargs) == ([], args[0])
    assert extract(*args, source_text=kwargs['source_text'].replace('lesquelles sont désormais liées', 'lesquelles sont désormais non liées')) == ([], args[0])


def test_no_historical_owner_in_isolation():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(5)
    for name, old_extract in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser457_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old_extract).parameters else {}
        events, rest = old_extract(*args, **options)
        assert events == [], name
        # Some old extractors normalize trailing punctuation without recognizing a rule.
        assert rest.strip(' ,.;') == args[0].strip(' ,.;'), name


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
        with patch.object(parser, 'extract_parser457_leftovers', lambda text, *a, **kw: ([], text)):
            old = parse_publication_xml(FIXTURES / name)
        assert result == old
    assert matched


def test_restriction_owner_deferred_even_in_isolation():
    from shab_analyzer.parser60 import _FR_SHARE_TRANSFER_RESTRICTION
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(5)
    text = args[0].rstrip(' . ,') + ', liées selon statuts'
    assert _FR_SHARE_TRANSFER_RESTRICTION.search(text)
    assert extract(text, *args[1:], **kwargs) == ([], text)
    path = FIXTURES / (DIGESTS[5] + '.xml')
    with patch.object(parser, 'extract_parser457_leftovers', lambda text, *a, **kw: ([], text)):
        with_pass = parse_publication_xml(path)
        with patch.object(parser, 'needs_legacy_restriction_pass', lambda *a: False):
            original = parse_publication_xml(path)
    assert with_pass.events == original.events
