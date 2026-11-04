import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser472 import extract_parser472_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '0fbc84ce3a1a78d531e814b858765f0113b47b4ae98c4592c4d757350d20853b', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser472_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser472_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 1:
        assert len(added) == 1
        assert result.events == old.events + added
        assert result.leftover_text == rest.strip(' .')
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 475
    _, _, (args, kwargs) = captured(1)
    events, rest = extract(*args, **kwargs)
    event, = events
    assert rest == ''
    assert event.event_type == 'capital_changed'
    assert event.rule_id == 'fr.text.registered_share_capital_after_restriction.v1'
    assert event.payload == {
        'kind': 'share_structure', 'currency': 'CHF', 'capital_total': "100'000",
        'paid': "100'000", 'paid_in_full': True, 'shares_count': 1000,
        'nominal': '100', 'share_kind': 'actions nominatives'}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None, **kwargs)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    legacy = Event(publication_id='legacy', published_at='', event_type='organization_changed',
                   rule_id='legacy', payload={'action': 'legacy'})
    assert Event(**vars(legacy)) == legacy


def test_old_rules_do_not_already_extract_this_capital_structure():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(1)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser472_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        if name == 'extract_parser60_leftovers':
            # This rule already emitted the restriction; it must remain unchanged.
            result, baseline, _ = captured(1)
            assert events and all(event in baseline.events for event in events)
            assert all(event in result.events for event in events)
        else:
            assert not events and rest == args[0], name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(1)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('nominatives', 'au porteur'),
                 args[0].replace("1'000", "'")):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'de', *args[2:], **kwargs) == ([], args[0])
    assert extract(*args) == ([], args[0])


@pytest.mark.parametrize('number,pattern', [
    (50, '_FR_SHARE_RESTRICTION_WITH_CAPITAL'),
    (54, '_FR_SHARE_CAPITAL_STRUCTURE'),
    (114, '_FR_REGISTERED_SHARE_RESTRICTION_STRUCTURE')])
def test_old_rules_keep_ownership(number, pattern):
    import importlib
    module = importlib.import_module(f'shab_analyzer.parser{number}')
    old_pattern = getattr(module, pattern)
    args = captured(1)[2][0]
    if number == 114:
        import shab_analyzer.parse as parser
        path = FIXTURES / 'cd82b5e5-7cdb-4461-9e0e-bed58f13a80a.xml'
        original = parser.extract_parser114_leftovers
        calls = []
        def capture(*a, **kw):
            calls.append((a, kw))
            return original(*a, **kw)
        with patch.object(parser, 'extract_parser114_leftovers', capture):
            result = parse_publication_xml(path)
        with patch.object(parser, 'extract_parser472_leftovers', lambda text, *a, **kw: ([], text)):
            assert result == parse_publication_xml(path)
        assert any(original(*a, **kw)[0] for a, kw in calls)
        for a, kw in calls:
            assert extract(*a, **kw) == ([], a[0])
        return
    found = False
    for path in FIXTURES.glob('*.xml'):
        # Use the historical fixtures only; compare pipeline outcomes relatively.
        import xml.etree.ElementTree as ET
        root = ET.parse(path).getroot()
        for element in root.iter():
            source = element.text or ''
            match = old_pattern.search(source)
            if not match:
                continue
            text = match[0]
            assert extract(text, *args[1:], source_text=source) == ([], text)
            import shab_analyzer.parse as parser
            result = parse_publication_xml(path)
            with patch.object(parser, 'extract_parser472_leftovers', lambda text, *a, **kw: ([], text)):
                assert result == parse_publication_xml(path)
            found = True
            break
        if found:
            break
    assert found
