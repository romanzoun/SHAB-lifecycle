import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser478 import extract_parser478_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '080904258c3de2949cd5f7ca3067c9659e34785f450bcd6ec110a13b387d9936', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser478_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser478_leftovers', lambda text, *a, **kw: ([], text)):
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


def test_payload_and_optional_metadata():
    assert PARSER_VERSION == 509
    _, _, (args, kwargs) = captured(1)
    events, rest = extract(*args, **kwargs)
    assert rest == '' and len(events) == 1
    event = events[0]
    assert event.event_type == 'branch_changed'
    assert event.payload == {'action': 'previous_branch_reference', 'previous_place': 'Altstätten'}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None, **kwargs)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    assert extract(*args) == ([], args[0])
    legacy = Event('legacy', '', 'branch_changed', 'legacy', payload={'action': 'added'})
    assert Event(**vars(legacy)) == legacy
    assert 'previous_place' not in legacy.payload


def test_no_old_rule_owns_input():
    import shab_analyzer.parse as parser
    from shab_analyzer.text_extras import extract_text_extras
    _, _, (args, kwargs) = captured(1)
    assert extract_text_extras(*args, set()) == ([], args[0])
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser478_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        assert old(*args, **options) == ([], args[0]), name


def test_unsupported_input():
    _, _, (args, kwargs) = captured(1)
    for text in ('', args[0] + ' UNKNOWN', '[bisher: Altstätten (HR SG)]'):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    for language in ('fr', 'it', None):
        assert extract(args[0], language, *args[2:], **kwargs) == ([], args[0])
    assert extract(*args, source_text='unrelated') == ([], args[0])


@pytest.mark.parametrize('text,module', [
    ('[bisher: Altstätten (HR SG)]', 'parser65'),
    ('[bisher: Altstätten (CH-320.9.123.456-7)]', 'parser85'),
])
def test_legacy_boundary(text, module):
    import importlib
    _, _, (args, kwargs) = captured(1)
    old = getattr(importlib.import_module('shab_analyzer.' + module), 'extract_' + module + '_leftovers')
    expected = old(text, *args[1:])
    assert expected[0]
    assert extract(text, *args[1:], **kwargs) == ([], text)
    assert old(extract(text, *args[1:], **kwargs)[1], *args[1:]) == expected


def test_legacy_pipeline_relative():
    import shab_analyzer.parse as parser
    path = FIXTURES / (DIGESTS[1] + '.xml')
    with patch.object(parser, 'extract_parser478_leftovers', lambda text, *a, **kw: ([], text)):
        expected = parse_publication_xml(path)
    # Without optional source context the new rule must leave the old pipeline intact.
    with patch.object(parser, 'extract_parser478_leftovers', lambda *a, **kw: extract(*a)):
        assert parse_publication_xml(path) == expected


def test_existing_branch_fixture_relative():
    import shab_analyzer.parse as parser
    path = FIXTURES / 'b8af5526-e821-4599-874e-8bc8160c2d99.xml'
    result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser478_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
