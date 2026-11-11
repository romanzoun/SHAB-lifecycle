import hashlib
import inspect
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pytest

from shab_analyzer.config import PARSER_VERSION
from shab_analyzer.models import Event
from shab_analyzer.parse import parse_publication_xml
from shab_analyzer.parser470 import extract_parser470_leftovers as extract

FIXTURES = Path(__file__).parent / 'fixtures'
DIGESTS = ['02d817cbe5e11478bb4d4ade72435c6e8f6ae90e1f03c6a84c0ce7c117920b11', '1c62f6659142a1fb2e04da93cb26ac590c465a51cf1e7c63694837d7859b228e', '2dba61731a7fb70cca1489ea446be3c1ce4222451defdbec6dbaaac847a1d0b3', '3e4cd556a1adc669b4d289ca2b1f0a8d78ddd3783d5f025cfb331d396d68e232', '6ee99f061701b8e967d9ab1bc86fcc654be0edf730a8303b8f25d0b01c123527', '7407e1df122944f0074d9a31ec44ed8c4dae455a2a3dbd4144cf0ea7b3319aad', '88b2cee5e9c911f384b16e040729d8cb2e042ba031faf36327bbdd440d0a88b7', '89ce6ac882c9cb489e7a27c564c70bcef445693584cf7ac4413b34ed9d8cc7cf', '8bb4f070db8be493d9d8774f0782f67efdbe36f44d408ddc67ebbdfbfb37152a', '8c809b987480c35880843a4b1f7667553c14ed4e998d18f71ad06f1ca999338f', 'a47f068fccf17e89d260d96f4c3463d344fb46e225c7abc93a14e94aa80bcad5', 'f01018b393073bf4f12a9a26dae061b80a79cc2b72109235e38d57c0b26beeed']


@lru_cache(None)
def captured(index):
    import shab_analyzer.parse as parser
    calls = []
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return extract(*args, **kwargs)
    path = FIXTURES / (DIGESTS[index] + '.xml')
    with patch.object(parser, 'extract_parser470_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser470_leftovers', lambda text, *a, **kw: ([], text)):
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
    if index == 8:
        assert len(added) == 1
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
    assert PARSER_VERSION == 525
    _, _, (args, kwargs) = captured(8)
    events, rest = extract(*args, **kwargs)
    event, = events
    assert rest == ''
    assert event.event_type == 'branch_changed'
    assert event.rule_id == 'de.text.branch_continuation_corrected_successor.v1'
    assert event.payload == {
        'action': 'business_continued_as_branch', 'successor': 'Netrics Biel AG',
        'previous_successor_name': 'netrics management AG', 'successor_place': 'Biel/Bienne',
        'successor_uid': 'CHE-109.492.437', 'legal_basis': 'Art. 112 HRegV', 'corrected': True}
    assert Event(**vars(event)) == event
    sparse, _ = extract(*args[:4], None, None, None, **kwargs)
    assert sparse[0].payload == event.payload
    assert sparse[0].org_uid is None and sparse[0].plz is None and sparse[0].canton is None
    legacy = Event(publication_id='legacy', published_at='', event_type='branch_changed',
                   rule_id='legacy', payload={'action': 'business_continued_as_branch'})
    assert Event(**vars(legacy)) == legacy


def test_no_old_rule_consumes_new_residue():
    import shab_analyzer.parse as parser
    _, _, (args, kwargs) = captured(8)
    for name, old in vars(parser).items():
        if not name.startswith('extract_parser') or name == 'extract_parser470_leftovers':
            continue
        options = kwargs if 'source_text' in inspect.signature(old).parameters else {}
        events, rest = old(*args, **options)
        assert not events and rest == args[0], name


def test_unsupported_input_unchanged():
    _, _, (args, kwargs) = captured(8)
    for text in ('', args[0] + ' UNKNOWN', '[' + args[0] + ']',
                 args[0].replace('112', '113'),
                 args[0].replace('weitergeführt', 'aufgehoben')):
        assert extract(text, *args[1:], **kwargs) == ([], text)
    assert extract(args[0], 'fr', *args[2:], **kwargs) == ([], args[0])
    assert extract(*args) == ([], args[0])
    for source in (kwargs['source_text'].replace('Berichtigung', 'Nachtrag', 1),
                   kwargs['source_text'].replace('CHE-109.492.437', 'CHE-109.492.438')):
        assert extract(*args, source_text=source) == ([], args[0])


@pytest.mark.parametrize('number,fixture', [
    (208, 'f5e4cff9-5a0a-49e8-be74-de8221037061'),
    (219, '03693f05-3bee-4765-bb86-a5825bed8e43'),
    (229, 'dd86ef1e-235b-4309-8599-7451ac6eaa8c'),
    (318, '7090c3ff'),
])
def test_old_rules_keep_ownership(number, fixture):
    import shab_analyzer.parse as parser
    path, = FIXTURES.glob(fixture + '*.xml')
    calls = []
    original = getattr(parser, f'extract_parser{number}_leftovers')
    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)
    with patch.object(parser, f'extract_parser{number}_leftovers', capture):
        result = parse_publication_xml(path)
    with patch.object(parser, 'extract_parser470_leftovers', lambda text, *a, **kw: ([], text)):
        baseline = parse_publication_xml(path)
    assert result == baseline
    assert calls
    assert any(original(*args, **kwargs)[0] for args, kwargs in calls)
    for args, kwargs in calls:
        assert extract(*args, **kwargs) == ([], args[0])
