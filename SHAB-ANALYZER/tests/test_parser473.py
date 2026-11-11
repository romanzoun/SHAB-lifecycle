import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser473 import extract_parser473_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6d198ec7ab6087c108bcaf47a90a426bfbd84546be6ec3ee867c20c0e4dde02b', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser473_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser473_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 4:
        assert len(added) == 2
        later = list(result.events)
        for event in old.events + added:
            later.remove(event)
        own = {event.rule_id for event in added}
        assert all(event.rule_id not in own for event in later)
        assert rest.strip(' .').endswith(result.leftover_text)
    else:
        assert (added, rest) == ([], args[0])
        assert result == old


def test_payload_and_missing_optional_metadata():
    assert PARSER_VERSION == 527
    _, _, (args, kwargs) = captured(4)
    events, rest = extract(*args, **kwargs)
    assert rest == ''
    removed, appointed = events
    assert [e.event_type for e in events] == ['officer_removed', 'officer_changed']
    assert all(e.rule_id == 'de.persons.unsigned_foundation_board_replacement.v1' for e in events)
    assert removed.payload == {'name': 'Rytz Maja', 'place': None, 'action': 'removed'}
    assert appointed.payload == {'name': 'Herren Ursula', 'place': 'Murten', 'action': 'appointed', 'heimat': 'Murten'}
    assert all(e.role == 'Stiftungsratsmitglied' and e.signing == 'ohne Unterschrift' for e in events)
    assert all(Event(**vars(e)) == e for e in events)
    sparse, _ = extract(*args[:4], None, None, None)
    assert [e.payload for e in sparse] == [e.payload for e in events]
    assert all(e.org_uid is None and e.plz is None and e.canton is None for e in sparse)
    legacy = Event(publication_id='legacy', published_at='', event_type='officer_changed',
                   rule_id='legacy', payload={'name': 'Legacy Person'})
    assert Event(**vars(legacy)) == legacy


def test_no_old_extractor_already_owns_new_input():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(4)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser473_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert (events, rest) == ([], args[0]), name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(4)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('ohne Unterschrift', 'Einzelunterschrift'),
                 args[0].replace('Stiftungsratsmitglied', 'Verwaltungsratsmitglied'),
                 args[0].replace('von und in', 'in')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'it', *args[2:], **kwargs) == ([], args[0])


@pytest.mark.parametrize('text', [
    'Gelöschte Person: Muster Anna, Stiftungsratsmitglied, ohne Unterschrift. '
    'Eingetragene Person geändert: Muster Beat, Stiftungsratsmitglied, ohne Unterschrift, '
    'neu Präsident, Einzelunterschrift. Neu eingetragene Person: Muster Clara, '
    'von und in Bern, Stiftungsratsmitglied, ohne Unterschrift',
    'Gelöschte Person: Muster Anna, Kollektivunterschrift zu zweien. '
    'Neu eingetragene Person: Muster Clara, von Bern, in Bern, Kollektivunterschrift zu zweien',
])
def test_legacy_patterns_keep_ownership(text):
    from shab_analyzer.parser63 import _DE_MIXED_PERSON_CHANGES
    from shab_analyzer.parser95 import _DE_MIXED_PERSON_REPLACEMENT
    assert any(p.fullmatch(text) for p in (_DE_MIXED_PERSON_CHANGES, _DE_MIXED_PERSON_REPLACEMENT))
    assert extract(text, 'de', 'test', '', None, None, None) == ([], text)


@pytest.mark.parametrize('stem', [
    '13581c01-eaea-4ff9-b412-8052ea1d7d2b',
    '639f3299-b635-441a-a831-5d7e44b9cd65',
    '7d6f1584-a6d8-4634-8585-0a66da9d7269',
])
def test_legacy_pipeline_unchanged(stem):
    import shab_analyzer.parse as parser
    path = FIXTURES / (stem + '.xml')
    calls = []
    def capture(*a, **kw):
        calls.append((a, kw))
        return extract(*a, **kw)
    with patch.object(parser, 'extract_parser473_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser473_leftovers', lambda text, *a, **kw: ([], text)):
        assert result == parse_publication_xml(path)
    assert calls
    for args, kwargs in calls:
        assert extract(*args, **kwargs) == ([], args[0])
